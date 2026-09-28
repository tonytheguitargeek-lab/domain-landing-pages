---
title: Beyer Headsets
category: headsets-intercom
summary: A recommended video on troubleshooting Clear-Com intercom headsets, including DT-108 single-muff headsets, and the workflow that led to a pocket headset tester idea.
video_title: Beyer Headsets
video_url: https://www.youtube.com/watch?v=ax9RFZRh3fA
creator: n392ep
covers:
  - Troubleshooting Clear-Com intercom headsets
  - DT-108 single-muff headsets
---

Intercom headsets are some of the hardest-working gear on any show, and when one acts up it tends to be at the worst possible moment. This video from the n392ep channel covers troubleshooting headsets used on Clear-Com intercom, including DT-108 single-muff headsets.

## Why I recommend it

It comes from the same channel as the [Triax Connectors](../triax-connectors/) video: someone I've worked with and consider a very good broadcast resource. It's a clear look at working through a headset problem methodically instead of guessing.

## Where this led: a pocket headset tester

This video, and the multimeter troubleshooting workflow that goes with it, helped lead to the idea for a dedicated pocket broadcast headset tester. That project is still on the bench. Details will be posted here once there's something real to show.

### What the tester should check

The useful field question isn’t “what is the exact impedance?” It’s whether the mic element is there, the ear elements are there, and the wiring makes sense for this headset type.

For the camera headsets I’ve checked, the mic pair reads very low resistance, while the ear elements are around the 50–60 ohm range individually. A double-muff headset also gives you the expected series relationship across both ear elements.

That gives a dedicated tester enough information to make a quick PASS / FAIL decision without dragging out a meter and remembering pin combinations.

## Field notes

My own observations from headset troubleshooting in the field.

### Headset faults that come up most

The failures worth catching quickly are the simple field failures: an open ear element, an open mic path, a broken conductor, a bad connector, or a wiring condition that doesn’t match what a known-good headset should show.

A multimeter will find those, but it takes time and you need to remember which pins to probe. That’s what made a dedicated pocket tester appealing: plug the headset in, press one button, and get a quick answer.

### Multimeter checklist for a 5-pin camera headset

Before the dedicated tester concept, the manual check was basically:

- Verify the microphone pair has continuity and a plausible resistance.
- Verify each ear element has the expected resistance.
- On a double-muff headset, verify the relationship between the two ear elements makes sense.
- Check for shorts between circuits that should be isolated.
- Check shield/connector wiring for anything unexpected.
- Compare against a known-good headset when there’s any doubt.

### Known-good measurements from the tester project

Pin-to-pin readings from the 5-pin camera headsets checked for the tester project. They're reference points for those headsets, not a spec for every model; when in doubt, compare against a known-good headset of the same type.

**Double-muff headset**

- `1–2` = 0.196
- `3–4` = 52.0
- `3–5` = 52.0
- `4–5` = 103
- All other combinations open, including shield

**Single-muff headset**

- `1–2` = 0.186
- `3–4` = 57.6
- All other combinations open, including shield
