# Synthetic Data Design

Entities:

- Customer
- Account
- PaymentInstrument
- Device
- IpCluster
- Merchant
- MerchantCategory
- Transaction
- Refund
- Chargeback
- Dispute
- SupportContact
- AccountChange
- FraudRing
- Alert
- Case
- Investigator

The MVP materializes the main operational entities directly and derives refunds,
chargebacks, alerts, and cases from transactions.

## Benign Personas

- Normal consumer
- High-spend traveler
- Small business buyer
- Seasonal shopper
- Refund-heavy but legitimate customer
- New account with legitimate growth
- Subscription-heavy user
- Cross-border legitimate user

## Synthetic Ring Types

- Mule network
- Refund abuse ring
- Account-takeover-like cluster, abstract only
- Synthetic identity ring
- Collusive merchant cluster
- Promo/bonus abuse ring
- Chargeback abuse cluster

All ring behavior is abstract and synthetic. The simulator does not describe real-world
fraud execution.

