# Contract-terms notes (for the quote; kept by the cloud worker, lead order 39 item 2)

1. Queue service time. The client contract must require that a person answers a chat handed to the queue in a time shorter than `conversations_days` (default 30 days). Without it, the age-out purge can delete a chat whose "needs a person" item is still open (AK-G1 design NEEDS LEAD 2, option (a)+(c)).
