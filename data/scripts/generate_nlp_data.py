"""
Phase 1 — Generate a synthetic LIAR-style fake/real news dataset.
This gives us a working pipeline; swap with real LIAR+FakeNewsNet later.
"""

import csv
import random
from pathlib import Path

random.seed(42)

# --- Templates ---
# Each template is (label, text_generator)

REAL_TEMPLATES = [
    "The {org} announced today that {policy}.",
    "According to {org}, the {metric} has {direction} by {pct}% compared to last year.",
    "{org} confirmed that {event} will take place in {city} next {time}.",
    "In a statement released {time}, {org} said {policy}.",
    "The {org} reported {pct} {unit} growth in {sector} during the {period}.",
    "New data from {org} shows that {event} affected approximately {num} {people} in {region}.",
    "{org} has approved a new {policy} that will {action} starting {time}.",
    "Researchers at {org} published a study showing {finding}.",
    "The {org} held a press conference to address {event}.",
    "Local authorities in {city} confirmed that {event}.",
    "{org} released its quarterly report showing {finding}.",
    "The committee voted {pct}-to-{num} in favor of {policy}.",
    "According to the latest {metric}, {sector} has remained stable over {period}.",
    "The {org} meeting concluded with {event}.",
    "Officials from {org} stated that {policy} is expected to take effect {time}.",
    "A new {sector} report by {org} indicates {finding}.",
    "The {org} published guidelines recommending {policy}.",
    "Data collected over {period} confirms that {finding}.",
    "{org} announced a partnership with {org2} to {action}.",
    "The {org} survey found that {pct}% of {people} support {policy}.",
    "In {city}, the {org} opened a new facility aimed at {action}.",
    "{org} released a statement clarifying {event}.",
    "The board of directors at {org} approved {policy}.",
    "A report by {org} found that {finding}.",
    "The {org} confirmed plans to {action} by {time}.",
]

FAKE_TEMPLATES = [
    "SHOCKING: {org} is secretly {action} — {org2} tries to COVER IT UP!!!",
    "You WON'T BELIEVE what {org} just did to {people}! {policy} is a LIE!",
    "BREAKING: {org} caught {action} — mainstream media SILENT!!!",
    "EXPOSED: {org} has been {action} for {pct} years, {org2} knew ALL ALONG!!!",
    "URGENT: {org} announces {policy} — this is what they DON'T want you to know!",
    "EXCLUSIVE: {org} caught fabricating {metric} data — {pct}% of their reports are FAKE!",
    "MUST READ: {org} is planning to {action} and {org2} is HELPING them!",
    "EXPOSED: {org} has been lying about {finding} — leaked documents prove it!",
    "ALERT: {org} caught secretly {action} — {org2} won't investigate!",
    "LEAKED: {org} internal memo reveals {policy} is a complete HOAX!",
    "EXPOSED: {org} has been {action} — mainstream media REFUSES to report!",
    "BREAKING: {org} announces {policy} — the REAL reason will SHOCK you!",
    "CONFIRMED: {org} caught fabricating {metric} — {pct}% of {people} are being DECEIVED!",
    "URGENT: {org} caught {action} — they're trying to silence {org2}!",
    "SHOCKING: {org} has been {action} for years — {org2} covered it all up!",
    "EXPOSED: {org} fake {metric} data — {pct}% of their claims are VERIFIED FALSE!",
    "BREAKING: {org} announces {policy} — this is a DIRECT ATTACK on {people}!",
    "LEAKED: {org} caught {action} — {org2} helped them HIDE the evidence!",
    "EXCLUSIVE: {org} fabricating {metric} — {pct}% of their reports are PROVEN FAKE!",
    "ALERT: {org} caught secretly {action} — {org2} is COMPLICIT!",
    "MUST READ: {org} has been {action} — this is what they DON'T want you to see!",
    "CONFIRMED: {org} fake {metric} data — {pct}% of {people} are being LIED TO!",
    "URGENT: {org} caught {action} — mainstream media won't touch this story!",
    "BREAKING: {org} announces {policy} — the TRUTH they're hiding will SHOCK you!",
    "EXPOSED: {org} fabricating data — leaked documents PROVE it's all a HOAX!",
    "SHOCKING: {org} caught {action} — {org2} helped COVER IT UP for {pct} years!",
    "LEAKED: {org} internal documents reveal {policy} is COMPLETELY FAKE!",
    "EXCLUSIVE: {org} caught fabricating {metric} — {pct}% of their claims are FALSE!",
    "CONFIRMED: {org} has been {action} — {org2} knew about it and said NOTHING!",
    "ALERT: {org} caught {action} — they're DESPERATE to hide the truth from {people}!",
]

FILLERS = {
    "org": ["Federal Reserve", "World Health Organization", "NASA", "CDC",
            "Department of Education", "EPA", "FDA", "Pentagon", "UN",
            "European Union", "FBI", "SEC", "FEMA", "NIH", "NSA"],
    "org2": ["independent researchers", "congressional leaders", "international observers",
             "press agencies", "privacy advocates", "state officials", "journalists",
             "whistleblowers", "internal staff", "external auditors"],
    "policy": ["a new trade agreement", "revised emission standards", "updated guidance",
               "stricter regulations", "a relief package", "a regulatory framework",
               "a moratorium on drilling", "a minimum wage increase", "budget cuts"],
    "metric": ["employment", "inflation", "GDP", "deficit", "trade balance",
               "unemployment", "revenue", "growth", "spending", "output"],
    "direction": ["increased", "decreased", "remained steady", "improved", "declined"],
    "pct": [str(random.randint(2, 45)) for _ in range(20)],
    "event": ["the signing of a new agreement", "a major policy shift",
              "budget allocations for next year", "a new research initiative",
              "an emergency response plan", "a public consultation"],
    "city": ["Washington", "New York", "London", "Brussels", "Tokyo",
             "Berlin", "Paris", "Beijing", "Ottawa", "Canberra"],
    "time": ["Monday", "Tuesday", "Wednesday", "next week", "next quarter",
             "early 2027", "by end of year", "this summer"],
    "unit": ["percent", "points", "billion dollars", "million units"],
    "sector": ["technology", "healthcare", "energy", "finance", "manufacturing",
               "agriculture", "retail", "construction", "transportation"],
    "period": ["Q1 2026", "Q2 2026", "the first half of 2026",
               "the past quarter", "the last fiscal year"],
    "num": [str(random.randint(2, 50)) for _ in range(20)],
    "people": ["Americans", "EU citizens", "consumers", "small businesses",
               "taxpayers", "workers", "patients", "students", "residents"],
    "region": ["North America", "Europe", "the Asia-Pacific region",
               "sub-Saharan Africa", "Latin America"],
    "action": ["implementing new measures", "securing additional funding",
               "reducing emissions", "expanding operations", "improving safety standards",
               "increasing transparency", "modernizing infrastructure"],
    "finding": ["a correlation between air quality and public health",
                "significant improvements in test scores",
                "a decline in reported incidents",
                "a 15% increase in renewable energy adoption",
                "reduced wait times for public services",
                "improved outcomes for patients"],
}


def fill_template(template: str) -> str:
    """Fill a template with random filler values."""
    result = template
    for key, values in FILLERS.items():
        placeholder = "{" + key + "}"
        while placeholder in result:
            result = result.replace(placeholder, random.choice(values), 1)
    return result


def generate_dataset(n_samples: int = 10000) -> list:
    """Generate a balanced fake/real dataset."""
    data = []
    half = n_samples // 2

    for _ in range(half):
        template = random.choice(REAL_TEMPLATES)
        text = fill_template(template)
        data.append({"text": text, "label": "real"})

    for _ in range(half):
        template = random.choice(FAKE_TEMPLATES)
        text = fill_template(template)
        data.append({"text": text, "label": "fake"})

    random.shuffle(data)
    return data


def save_dataset(data: list, output_path: str, split: str = "train"):
    """Save dataset to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} samples to {path}")


def main():
    print("Generating synthetic LIAR-style dataset...")

    all_data = generate_dataset(n_samples=10000)

    # Split: 80% train, 10% val, 10% test
    random.shuffle(all_data)
    n = len(all_data)
    train = all_data[:int(n * 0.8)]
    val = all_data[int(n * 0.8):int(n * 0.9)]
    test = all_data[int(n * 0.9):]

    save_dataset(train, "data/processed/nlp_train.csv", "train")
    save_dataset(val, "data/processed/nlp_val.csv", "val")
    save_dataset(test, "data/processed/nlp_test.csv", "test")

    # Show sample
    print("\nSample real:", random.choice([d for d in all_data if d["label"] == "real"])["text"][:80])
    print("Sample fake:", random.choice([d for d in all_data if d["label"] == "fake"])["text"][:80])
    print(f"\nTotal: {n} | Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")


if __name__ == "__main__":
    main()
