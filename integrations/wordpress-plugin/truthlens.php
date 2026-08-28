<?php
/**
 * Plugin Name: TruthLens — Misinformation Detector
 * Description: Analyze articles and comments for misinformation using TruthLens AI
 * Version: 1.0.0
 * Author: TruthLens
 * License: MIT
 */

if (!defined('ABSPATH')) exit;

class TruthLens_Plugin {
    private $api_url;

    public function __construct() {
        $this->api_url = get_option('truthlens_api_url', 'http://localhost:8000');
        add_action('admin_menu', [$this, 'add_menu']);
        add_action('admin_init', [$this, 'register_settings']);
        add_shortcode('truthlens_analyze', [$this, 'shortcode']);
        
        // Add analysis button to post editor
        add_action('media_buttons', [$this, 'add_analysis_button']);
        add_action('admin_footer', [$this, 'add_inline_script']);
    }

    public function add_menu() {
        add_options_page(
            'TruthLens Settings',
            'TruthLens',
            'manage_options',
            'truthlens',
            [$this, 'settings_page']
        );
    }

    public function register_settings() {
        register_setting('truthlens_options', 'truthlens_api_url');
    }

    public function settings_page() {
        ?>
        <div class="wrap">
            <h1>TruthLens Settings</h1>
            <form method="post" action="options.php">
                <?php settings_fields('truthlens_options'); ?>
                <table class="form-table">
                    <tr>
                        <th>API URL</th>
                        <td>
                            <input type="text" name="truthlens_api_url" 
                                   value="<?php echo esc_attr($this->api_url); ?>"
                                   class="regular-text" />
                            <p class="description">TruthLens API endpoint</p>
                        </td>
                    </tr>
                    <tr>
                        <th>Test Connection</th>
                        <td>
                            <button type="button" class="button" id="tl-test">Test</button>
                            <span id="tl-test-result"></span>
                        </td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
            <script>
            jQuery('#tl-test').click(function() {
                var url = jQuery('input[name="truthlens_api_url"]').val();
                jQuery.get(url + '/health', function(d) {
                    jQuery('#tl-test-result').html('<span style="color:green">Connected!</span>');
                }).fail(function() {
                    jQuery('#tl-test-result').html('<span style="color:red">Failed</span>');
                });
            });
            </script>
        </div>
        <?php
    }

    public function add_analysis_button($editor) {
        if (get_post_type() !== 'post') return;
        echo '<button type="button" id="truthlens-btn" class="button" style="margin-left:5px;">🔍 TruthLens</button>';
    }

    public function add_inline_script() {
        if (get_post_type() !== 'post') return;
        ?>
        <script>
        jQuery('#truthlens-btn').click(function() {
            var content = jQuery('#content').val();
            if (!content) { alert('No content to analyze'); return; }
            
            var text = content.replace(/<[^>]+>/g, '').substring(0, 5000);
            jQuery.post('http://localhost:8000/analyze', {text: text}, function(d) {
                var msg = 'Verdict: ' + d.verdict + ' (Score: ' + d.threat_score + '/100)\n\n';
                for (var mod in d.breakdown) {
                    if (d.breakdown[mod]) {
                        msg += mod.toUpperCase() + ': ' + d.breakdown[mod].label + 
                               ' (' + (d.breakdown[mod].confidence*100).toFixed(1) + '%)\n';
                    }
                }
                alert(msg);
            }).fail(function() { alert('TruthLens API not reachable'); });
        });
        </script>
        <?php
    }

    public function shortcode($atts) {
        $atts = shortcode_atts(['text' => ''], $atts);
        if (!$atts['text']) return '<p>No text provided</p>';

        $response = wp_remote_post($this->api_url . '/analyze', [
            'body' => ['text' => $atts['text']],
            'timeout' => 30,
        ]);

        if (is_wp_error($response)) {
            return '<p>Error: ' . $response->get_error_message() . '</p>';
        }

        $result = json_decode(wp_remote_retrieve_body($response), true);
        $score = $result['threat_score'] ?? 0;
        $verdict = $result['verdict'] ?? 'Unknown';

        $color = $score >= 70 ? '#ef4444' : ($score >= 30 ? '#f59e0b' : '#22c55e');

        return '<div style="background:#1e293b;color:#f1f5f9;padding:16px;border-radius:8px;border-left:4px solid ' . $color . ';">
            <strong>TruthLens:</strong> ' . esc_html($verdict) . ' (' . $score . '/100)
        </div>';
    }
}

new TruthLens_Plugin();
