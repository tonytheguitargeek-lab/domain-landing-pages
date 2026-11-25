---
title: Radio Gremlin: How I Accidentally Built a Mesh Operations Center
short_title: Radio Gremlin
seo_title: Radio Gremlin: How I Accidentally Built a Mesh Operations Center — Bad Audio Guy
kicker: New project
dek: An old iMac, a LoRa radio, a little artificial intelligence, and absolutely no adult supervision.
summary: How a Meshtastic radio, an old iMac and some AI-assisted coding turned into Radio Gremlin: a self-recovering mesh bot, a touchscreen monitor, and a mesh observatory with its own radar map.
feature_text: How I accidentally built a mesh operations center with an old iMac, a LoRa radio and a little AI.
date: 2026-11-24
author: Bad Audio Guy
hero_image: assets/projects/radio-gremlin/radio-gremlin-badge.webp
hero_alt: Radio Gremlin badge: a grinning gremlin in a radio-tower cap, aviator sunglasses and a headset, with a cigar, a broadcast truck and satellite dish behind, above the words "Radio Gremlin, Mesh Operations Center".
og_image: assets/projects/radio-gremlin/radio-gremlin-social.jpg
og_image_alt: Radio Gremlin: How I Accidentally Built a Mesh Operations Center, on Bad Audio Guy.
related:
  - All projects | projects/
  - Pocket headset tester build | field-notes/beyer-headsets/#building-the-pocket-tester
  - Field Notes | field-notes/
---

It's been a while since I've posted anything here on Bad Audio Guy. It's not that I haven't been building things. If anything, I've probably been building too many things.

My latest adventure started with Meshtastic, a little radio, and a curiosity about what I could actually do with it beyond sending text messages.

Somewhere along the way, things got slightly out of hand.

## Down the Rabbit Hole

I've spent a good portion of my career working with RF systems in television production. Everything from wireless cameras and mobile receive systems to some fairly interesting long-distance microwave projects.

So naturally, the idea of inexpensive, low-power radios communicating with each other without relying on cellular service got my attention.

For those unfamiliar with Meshtastic, it's an open-source communications platform that uses LoRa radio technology. Small, relatively inexpensive devices can exchange messages, share positions and relay information through a mesh network.

You don't need a cell tower or an internet connection for the basic radio network to work.

Of course, being me, simply sending messages between two radios wasn't going to keep me entertained for very long.

## Enter the Radio Gremlin

I started experimenting with a T-Beam radio and an open-source Python project called Meshing Around.

The software provides a number of automated functions that allow a Meshtastic node to respond to commands, provide information and interact with other users.

I named my node Radio Gremlin.

It wasn't long before I could send it a message from another radio and get a response containing signal strength and signal-to-noise information.

That alone was pretty cool, but I wanted to see more of what was happening behind the scenes.

## Building Mesh Command

I had one of those inexpensive ESP32 touchscreen displays commonly referred to as a Cheap Yellow Display, or CYD.

Rather than constantly looking at my phone or digging through a terminal window, why not build a dedicated little monitoring terminal?

With some AI-assisted coding, I developed an interface that communicates with the software running on my shop computer.

I called it Mesh Command.

The touchscreen provides:

- Live radio activity
- Node information
- Packet monitoring
- Signal strength and signal-to-noise readings
- Direct and relayed packet identification
- System status

It's essentially a little piece of homemade communications test equipment.

And if you've spent any time around broadcast engineers, you know we like things with screens, buttons and flashing lights.

## The Turd Gets a New Job

My shop computer is an older iMac that I've affectionately named The Turd.

Its internal drive gave up some time ago, and it now runs from an external SSD. It isn't exactly the latest and greatest piece of Apple hardware, but it still has plenty of useful life left in it.

Rather than buying another computer to operate Radio Gremlin, I decided to put the Turd to work.

Initially, the radio was connected directly to the computer via USB. The problem was that my shop isn't necessarily the best place to put an antenna.

The T-Beam supports Wi-Fi, so I moved the radio upstairs and established a network connection between it and the iMac.

No long USB cable. No additional computer. Just a radio positioned in a more convenient location and the software running downstairs.

Naturally, this introduced another problem.

## Houston, We Have a Connection Problem

The radio would occasionally drop its TCP connection.

Sometimes the software wouldn't recover properly, even though the radio was still connected to the network.

That's not particularly useful if you're trying to build something that runs unattended.

After some troubleshooting, I developed a separate watchdog program that monitors the connection, detects certain failures and automatically restarts the Radio Gremlin software when necessary.

I even deliberately powered down the radio to see what would happen.

The watchdog detected the failure, waited for the radio to become available and restarted the software.

It worked.

Now, instead of babysitting a terminal window, I have a system designed to recover from the connection problems I've encountered so far.

## Building the Mesh Observatory

At this point, I could see live activity on my little touchscreen, but I wanted to collect information over a longer period.

Who was out there?

When were they transmitting?

How strong were their signals?

Was I receiving them directly, through another radio, or through the internet-connected portion of the network?

That led to the creation of Mesh Observatory.

The Observatory is a locally hosted monitoring dashboard that collects information from Radio Gremlin and stores it in a persistent SQLite database.

Instead of losing everything when the radio or software restarts, I can build up a historical record of activity.

The dashboard now includes:

- System health monitoring
- Historical packet information
- RF node discovery
- Signal strength and SNR history
- Direct and relayed traffic identification
- Separate RF and MQTT traffic monitoring
- A searchable node directory
- Persistent GPS position records
- An interactive map called Mesh Radar

I've also added an optional audible notification for newly detected RF activity.

It's starting to feel less like a radio experiment and more like a miniature network operations center.

## Not Everything Is RF

One of the important distinctions in this project is separating actual over-the-air reception from information arriving through MQTT.

Meshtastic can use MQTT to exchange information over the internet. This makes it possible to observe activity from nodes far beyond the practical range of a local LoRa radio.

It's interesting, but I don't want to confuse internet-delivered information with actual RF reception.

The Observatory separates these types of traffic, allowing me to concentrate on what the radio itself is hearing.

I've also modified Radio Gremlin so that incoming MQTT text messages don't trigger automatic bot replies.

I'm interested in observing the network, not becoming the most annoying thing on it.

There is still a distinction between the bot not replying and the radio firmware potentially forwarding MQTT downlink traffic over RF. That's something to keep in mind when configuring an internet-connected mesh node.

## Mesh Radar

Once I started collecting node positions, the obvious next step was to put them on a map.

Mesh Radar allows me to display nodes within selectable distances of my station, filter different types of traffic and examine individual node information.

The system retains previously collected positions even if the radio is restarted or a node disappears from its current directory.

I've given the map a dark appearance to match the rest of the Observatory.

Does it look a little like something you'd find in a Cold War communications bunker?

Perhaps.

Was that intentional?

Absolutely.

## Mission Control

By this point, I had several little applications scattered across the desktop for starting and stopping the software, opening the dashboard and viewing logs.

It was getting messy.

So the final addition for this round of development was a native macOS application called Gremlin Control Center.

From one small window, I can start and stop the individual services, open the Observatory, view the Gremlin log and monitor the radio connection, watchdog and computer sleep-prevention process.

The Observatory even opens in its own dedicated window without the usual browser clutter.

Everything is now controlled from a single desktop icon, complete with a rather appropriate Radio Gremlin mascot.

The Turd officially has a mission.

## Inside the Build {#gallery}

Screenshots from the running system. Other people's node IDs are hidden, and the map is zoomed out so it doesn't point to my station. Select any image to open the full-size version.

::: gallery wide
image: projects/radio-gremlin/01-mesh-observatory.webp
kind: screenshot
title: Mesh Observatory
caption: System health at a glance: the Gremlin API, radio link, watchdog, collectors and database, plus running totals for nodes, MQTT traffic and packets.
alt: Mesh Observatory dashboard showing six green system health indicators (Gremlin API online, Radio TCP connected, watchdog running, collector active, database readable, GPS collector active) and counters for nodes, MQTT messages, packets, direct and relayed traffic.

image: projects/radio-gremlin/02-rf-watch.webp
kind: screenshot
title: RF Watch
caption: Only what the radio itself heard over the air, kept separate from MQTT. BT 0 is my own test radio; node IDs are hidden.
alt: RF Watch panel with counters for RF node IDs, RF packets, direct and relayed packets, and an RF node directory table listing first and last heard times, packet counts, RSSI and SNR, with node identifiers blacked out.

image: projects/radio-gremlin/03-mesh-radar.webp
kind: screenshot
title: Mesh Radar
caption: Every node with a saved position, zoomed out to the whole continent. Most of these arrive over MQTT rather than RF. My own station's marker is left off.
alt: Mesh Radar dark map of North America with blue and grey dots marking known mesh nodes, mostly across the eastern and central United States, with radius, source and fit controls above it.

image: projects/radio-gremlin/04-gremlin-control-center.webp
kind: screenshot
title: Gremlin Control Center
caption: One small window to start and stop the services, open the Observatory and check the radio link, watchdog and sleep prevention.
alt: Gremlin Control Center window showing Radio Gremlin and Mesh Observatory running, Radio TCP connected, recovery watchdog and sleep prevention active, with start, stop and open buttons.
:::

Hardware photos of the T-Beam and the Mesh Command touchscreen will be added in a future update.

## What Did AI Have to Do With All This?

Quite a bit, actually.

I've been experimenting with AI-assisted programming for several of my recent projects.

I'm not a professional software developer. My background is in broadcast engineering, troubleshooting, integration and making equipment do things it wasn't necessarily designed to do.

I understand what I want the system to accomplish. AI helps me translate those ideas into working software.

That doesn't mean everything works the first time.

There have been failed installations, connection problems, coding errors and plenty of trips back to the drawing board.

But that's part of the process.

I bring the engineering experience, the hardware, the ideas and the testing. AI helps with the programming and development.

The combination has allowed me to build things that would have taken me considerably longer to develop on my own.

## Where It Stands Today

As of November 24, 2026, the Observatory had collected more than 1,100 packets and identified over 540 node IDs.

Most of that activity came through MQTT, not directly over RF.

The RF monitoring system had recorded activity associated with three node IDs, including my own test radio and two unidentified nodes.

All of the system health indicators were showing normal operation when I wrapped up development for the evening.

The next step is simply to let it run.

I want to see what the radio hears overnight, how reliably the software operates and what happens when the system is left unattended for an extended period.

There's also plenty of room for future experimentation with antennas, coverage mapping, portable nodes and RF performance testing.

This isn't a finished commercial product. It's a personal experiment that keeps evolving.

## The Best Part

I didn't start out with a grand plan to build a mesh operations center.

I started with a radio and a question.

Then one question led to another.

That's what I enjoy about having a workshop. It isn't necessarily about building something that needs to exist. Sometimes it's about building something just to find out if you can.

And sometimes an old computer, a handful of inexpensive electronics and a little curiosity can turn into something surprisingly useful.

Welcome to Radio Gremlin.

More to come.

*— Bad Audio Guy*

::: roadmap Project log
## Project Updates {#updates}

New developments will be added here as Radio Gremlin keeps evolving.

- **November 24, 2026:** First write-up. Mesh Command, the watchdog, Mesh Observatory, Mesh Radar and Gremlin Control Center are all running. Next up: let it run unattended and see what the radio hears.
:::
