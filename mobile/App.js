/**
 * TruthLens Mobile App — React Native
 * On-the-go misinformation detection.
 */

import React, { useState, useEffect } from 'react';
import {
  SafeAreaView, Text, TextInput, TouchableOpacity, ScrollView,
  StyleSheet, ActivityIndicator, Image, Alert,
} from 'react-native';
import { analyzeText, analyzeImage, getHistory, healthCheck } from './src/api';
import { launchImageLibrary } from 'react-native-image-picker';

const VerdictBadge = ({ score, verdict }) => {
  const color = score >= 71 ? '#ef4444' : score >= 31 ? '#f59e0b' : '#22c55e';
  return (
    <View style={[styles.badge, { backgroundColor: color }]}>
      <Text style={styles.badgeText}>{verdict} — {score}/100</Text>
    </View>
  );
};

export default function App() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    healthCheck().then(() => setConnected(true)).catch(() => setConnected(false));
    getHistory(10).then(setHistory).catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const data = await analyzeText(text);
      setResult(data);
    } catch (e) {
      Alert.alert('Error', e.message);
    }
    setLoading(false);
  };

  const handleImage = async () => {
    const response = await launchImageLibrary({ mediaType: 'photo', quality: 0.8 });
    if (response.didCancel || !response.assets?.[0]) return;
    setLoading(true);
    try {
      const data = await analyzeImage(response.assets[0].uri);
      setResult(data);
    } catch (e) {
      Alert.alert('Error', e.message);
    }
    setLoading(false);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <Text style={styles.title}>🔍 TruthLens</Text>
        <Text style={styles.subtitle}>
          {connected ? '✅ Connected to API' : '❌ API not reachable'}
        </Text>

        <TextInput
          style={styles.input}
          placeholder="Paste text to analyze..."
          placeholderTextColor="#64748b"
          multiline
          value={text}
          onChangeText={setText}
        />

        <TouchableOpacity style={styles.btn} onPress={handleAnalyze} disabled={loading}>
          {loading ? <ActivityIndicator color="white" /> : <Text style={styles.btnText}>🔎 Analyze Text</Text>}
        </TouchableOpacity>

        <TouchableOpacity style={[styles.btn, { backgroundColor: '#475569' }]} onPress={handleImage}>
          <Text style={styles.btnText}>🖼️ Analyze Image</Text>
        </TouchableOpacity>

        {result && (
          <View style={styles.result}>
            <VerdictBadge score={result.threat_score} verdict={result.verdict} />
            {result.breakdown && Object.entries(result.breakdown).map(([mod, data]) => (
              data && <Text key={mod} style={styles.breakdown}>
                {mod}: {data.label} ({(data.confidence * 100).toFixed(0)}%)
              </Text>
            ))}
          </View>
        )}

        <Text style={styles.sectionTitle}>Recent Analyses</Text>
        {history.map((h, i) => (
          <TouchableOpacity key={i} style={styles.historyItem}
            onPress={() => setResult(h)}>
            <Text style={styles.historyVerdict}>{h.verdict}</Text>
            <Text style={styles.historyScore}>{h.threat_score}/100</Text>
            <Text style={styles.historyTime}>{new Date(h.timestamp).toLocaleString()}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const View = require('react-native').View;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f172a', padding: 16 },
  title: { fontSize: 28, fontWeight: '700', color: '#60a5fa', textAlign: 'center', marginTop: 8 },
  subtitle: { fontSize: 12, color: '#64748b', textAlign: 'center', marginBottom: 16 },
  input: { backgroundColor: '#1e293b', borderRadius: 12, padding: 14, color: '#e2e8f0', fontSize: 14, minHeight: 100, textAlignVertical: 'top', borderWidth: 1, borderColor: '#334155' },
  btn: { backgroundColor: '#2563eb', borderRadius: 10, padding: 14, alignItems: 'center', marginTop: 10 },
  btnText: { color: 'white', fontSize: 15, fontWeight: '600' },
  result: { marginTop: 16, backgroundColor: '#1e293b', borderRadius: 12, padding: 16, borderWidth: 1, borderColor: '#334155' },
  badge: { borderRadius: 8, padding: 10, alignItems: 'center', marginBottom: 8 },
  badgeText: { color: 'white', fontWeight: '700', fontSize: 16 },
  breakdown: { color: '#94a3b8', fontSize: 13, marginLeft: 8, marginTop: 2 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#94a3b8', marginTop: 24, marginBottom: 8 },
  historyItem: { backgroundColor: '#1e293b', borderRadius: 8, padding: 12, marginBottom: 6, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  historyVerdict: { color: '#e2e8f0', fontWeight: '600', fontSize: 13 },
  historyScore: { color: '#60a5fa', fontSize: 13 },
  historyTime: { color: '#64748b', fontSize: 11 },
});
