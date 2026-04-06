# Flashcards

<!-- Section: Web Fundamentals -->

## What does the HTTP 503 status code mean?
<!-- id: 001 -->
---
Service Unavailable. The server is temporarily unable to handle the request, usually due to maintenance or overload. Unlike 500, it implies the condition is temporary.

## What is the difference between TCP and UDP?
<!-- id: 002 -->
---
TCP is connection-oriented and guarantees delivery through acknowledgments and retransmission. UDP is connectionless and does not guarantee delivery.

TCP is used when reliability matters (HTTP, file transfer). UDP is used when speed matters more than completeness (video streaming, DNS lookups).

## What does the CAP theorem state?
<!-- id: 003 -->
---
A distributed system can provide at most two of three guarantees simultaneously: Consistency, Availability, and Partition tolerance. Since network partitions are inevitable, you must choose between consistency and availability.

## What is a race condition?
<!-- id: 004 -->
---
A bug where the system's behavior depends on the timing or ordering of uncontrollable events. Two or more operations compete to access shared state, and the outcome changes depending on which finishes first.

<!-- Section: Concepts -->

## What is the bystander effect?
<!-- id: 005 -->
---
The tendency for individuals to be less likely to help when others are present. Diffusion of responsibility — each person assumes someone else will act. The larger the group, the stronger the effect.

## A card with no special formatting
<!-- id: 006 -->
---
This is a simple card with plain text.

## A multi-line front card
<!-- id: 008 -->
with a second line of context
and a third
---
This card has a multi-line front.

## A card with malformed metadata
not a metadata comment
This card should be skipped because it has no --- separator.

## A card with an empty back
<!-- id: 007 -->
---
