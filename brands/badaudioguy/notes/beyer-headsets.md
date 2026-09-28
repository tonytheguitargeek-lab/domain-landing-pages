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

For the camera headsets I’ve checked, a known-good mic pair reads approximately 186–196 ohms, and each ear element reads approximately 52–58 ohms. A double-muff headset also gives you the expected series path across both ear elements, approximately 103 ohms.

That gives a dedicated tester enough information to make a quick PASS / FAIL decision without dragging out a meter and remembering pin combinations.

## Building the Pocket Tester

The first prototype, from board design to a printed case in hand. Select any image to open the full-size version.

::: gallery
image: projects/headset-tester/01-rev-a3-pcb-render.png
kind: render
title: PCB design
caption: Rev A3 board design, prepared for fabrication.
alt: KiCad 3D render of the green Rev A3 headset tester circuit board, with the microcontroller in the middle, three LED positions labelled MIC, EAR1 and EAR2, and a row of pads for the 5-pin XLR, programming and power.

image: projects/headset-tester/02-enclosure-exploded-render.png
kind: render
title: Enclosure design
caption: Approved enclosure concept, exploded to show the PCB, XLR connector and cover.
alt: Exploded 3D render of the black prototype enclosure, with the 5-pin XLR connector at one end, the green circuit board beneath the case, and the bottom cover separated below.

image: projects/headset-tester/03-xlr-fit-test-plate.jpg
kind: photo
title: Connector fit test
caption: A small printed test plate was used to get the 5-pin XLR cut-out right before committing to the full case.
alt: Black 3D-printed test plate held between two fingers, with a female 5-pin XLR panel connector mounted in its cut-out.

image: projects/headset-tester/04-first-wired-case.jpg
kind: photo
title: First wired case
caption: Early printed enclosure with the XLR connector and test button installed.
alt: Open black 3D-printed case held in one hand, with the XLR connector fitted at the top end and a metal push button wired in with red and black leads.

image: projects/headset-tester/05-closed-prototype.jpg
kind: photo
title: Closed prototype
caption: Prototype case closed up, with the test button and three LED positions visible.
alt: Top of the closed black 3D-printed prototype case, showing a round stainless test button with three small LED holes above it.

image: projects/headset-tester/06-in-hand.jpg
kind: photo
title: In hand
caption: The enclosure was sized around one-handed field use.
alt: Hand holding the closed prototype case, with the thumb resting on the test button.
:::

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

- Known-good mic pair: approximately 186–196 ohms
- Ear element: approximately 52–58 ohms
- Double-muff series path: approximately 103 ohms

The mic-pair readings were taken on the meter's kΩ range (0.196 and 0.186 kΩ) and are shown below in ohms.

**Double-muff headset**

- `1–2` = 196 ohms
- `3–4` = 52.0 ohms
- `3–5` = 52.0 ohms
- `4–5` = 103 ohms
- All other combinations open, including shield

**Single-muff headset**

- `1–2` = 186 ohms
- `3–4` = 57.6 ohms
- All other combinations open, including shield
