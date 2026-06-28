from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from fraudwar.arena.environment import EXPERIMENTS, run_all, run_experiment
from fraudwar.synthetic.generator import SyntheticWorld, generate_world


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(prog="fraudwar")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    gen = sub.add_parser("generate-world")
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--accounts", type=int, default=10_000)
    gen.add_argument("--merchants", type=int, default=500)
    gen.add_argument("--transactions", type=int, default=100_000)
    gen.add_argument("--rings", type=int, default=10)
    gen.add_argument("--rich", action="store_true", help="Use rich Pydantic materialization for large exports.")
    sub.add_parser("list-experiments")
    run = sub.add_parser("run")
    run.add_argument("experiment", choices=EXPERIMENTS.keys())
    sub.add_parser("run-all")
    report = sub.add_parser("report")
    report.add_argument("run_id")
    sub.add_parser("export-demo")
    sub.add_parser("serve")
    args = parser.parse_args()

    if args.command == "init":
        print("FraudWar Room initialized. All data generated locally and synthetically.")
    elif args.command == "generate-world":
        out = ROOT / "data" / "generated" / f"world_seed_{args.seed}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        if args.rich or args.transactions < 50_000:
            world = generate_world(args.seed, args.accounts, args.merchants, args.transactions, args.rings)
            _write_world_json(world, out)
            summary = {
                "path": str(out),
                "mode": "rich",
                "accounts": len(world.accounts),
                "merchants": len(world.merchants),
                "transactions": len(world.transactions),
                "rings": len(world.rings),
                "refunds": len(world.refunds),
                "chargebacks": len(world.chargebacks),
                "disputes": len(world.disputes),
            }
        else:
            summary = _write_fast_world_json(
                out,
                seed=args.seed,
                account_count=args.accounts,
                merchant_count=args.merchants,
                transaction_count=args.transactions,
                ring_count=args.rings,
            )
        print(json.dumps(summary))
    elif args.command == "list-experiments":
        for key, value in EXPERIMENTS.items():
            print(f"{key}: {value}")
    elif args.command == "run":
        result = run_experiment(args.experiment, output_dir=ROOT / "data" / "generated")
        print(result["run_id"])
    elif args.command == "run-all":
        results = run_all(ROOT / "data" / "generated")
        print("\n".join(run["run_id"] for run in results))
    elif args.command == "report":
        report_path = ROOT / "data" / "generated" / "reports" / f"{args.run_id}_after_action.md"
        print(report_path)
    elif args.command == "export-demo":
        result = run_experiment(
            "static-vs-adaptive",
            output_dir=ROOT / "data" / "demo",
            accounts=350,
            merchants=45,
            transactions=1500,
            rings=4,
            days=20,
        )
        print(result["run_id"])
    elif args.command == "serve":
        import uvicorn

        uvicorn.run("fraudwar.main:app", host="127.0.0.1", port=8000, reload=True)


def _write_world_json(world: SyntheticWorld, out: Path) -> None:
    collections = [
        ("customers", world.customers),
        ("accounts", world.accounts),
        ("payment_instruments", world.payment_instruments),
        ("devices", world.devices),
        ("ip_clusters", world.ip_clusters),
        ("merchant_categories", world.merchant_categories),
        ("merchants", world.merchants),
        ("rings", world.rings),
        ("transactions", world.transactions),
        ("refunds", world.refunds),
        ("chargebacks", world.chargebacks),
        ("disputes", world.disputes),
        ("support_contacts", world.support_contacts),
        ("account_changes", world.account_changes),
    ]
    with out.open("w", encoding="utf-8") as handle:
        handle.write("{")
        for collection_index, (name, records) in enumerate(collections):
            if collection_index:
                handle.write(",")
            handle.write(json.dumps(name))
            handle.write(":[")
            for record_index, record in enumerate(records):
                if record_index:
                    handle.write(",")
                handle.write(record.model_dump_json())
            handle.write("]")
        handle.write("}")


def _write_fast_world_json(
    out: Path,
    seed: int,
    account_count: int,
    merchant_count: int,
    transaction_count: int,
    ring_count: int,
    days: int = 30,
) -> dict:
    rng = random.Random(seed)
    regions = ["NA", "EU", "LATAM", "APAC"]
    personas = [
        "normal_consumer",
        "high_spend_traveler",
        "small_business_buyer",
        "seasonal_shopper",
        "refund_heavy_legitimate",
        "new_account_legitimate_growth",
        "subscription_heavy_user",
        "cross_border_legitimate_user",
    ]
    categories = [
        "electronics",
        "travel",
        "apparel",
        "home",
        "digital_goods",
        "marketplace",
        "grocery",
        "subscription",
        "luxury",
    ]
    account_ids = [f"acct_{idx:06d}" for idx in range(account_count)]
    merchant_ids = [f"merch_{idx:05d}" for idx in range(merchant_count)]
    ring_members: dict[str, str] = {}
    ring_rows = []
    cursor = 0
    for ring_idx in range(ring_count):
        size = 24 + (ring_idx * 11) % 72
        members = account_ids[cursor : cursor + size]
        cursor += size
        ring_id = f"ring_{ring_idx:03d}"
        for account_id in members:
            ring_members[account_id] = ring_id
        ring_rows.append(
            {
                "ring_id": ring_id,
                "ring_type": [
                    "mule_network",
                    "refund_abuse_ring",
                    "account_takeover_cluster",
                    "synthetic_identity_ring",
                    "collusive_merchant_cluster",
                    "promo_bonus_abuse_ring",
                    "chargeback_abuse_cluster",
                ][ring_idx % 7],
                "start_day": ring_idx % 10,
                "active": True,
                "adaptation_strategy": "fragment_network",
                "members": members,
                "merchants": merchant_ids[ring_idx : ring_idx + 4],
                "shared_devices": [f"ring_dev_{ring_idx:03d}_{j}" for j in range(3)],
                "shared_ip_clusters": [f"ring_ip_{ring_idx:03d}_{j}" for j in range(2)],
                "detected": False,
                "disrupted": False,
            }
        )
    refunds = []
    chargebacks = []
    disputes = []
    support_contacts = []
    account_changes = []

    with out.open("w", encoding="utf-8") as handle:
        handle.write("{")
        _write_fast_collection(
            handle,
            "customers",
            (
                {
                    "customer_id": f"cust_{idx:06d}",
                    "region": regions[idx % len(regions)],
                    "legitimate_persona": personas[idx % len(personas)],
                    "created_day": -rng.randint(1, 900),
                    "risk_segment": "high" if idx % 37 == 0 else "medium" if idx % 7 == 0 else "low",
                }
                for idx in range(account_count)
            ),
        )
        handle.write(",")
        _write_fast_collection(
            handle,
            "accounts",
            (
                {
                    "account_id": account_id,
                    "customer_id": f"cust_{idx:06d}",
                    "created_day": -rng.randint(1, 900),
                    "region": regions[idx % len(regions)],
                    "risk_segment": "high" if idx % 37 == 0 else "medium" if idx % 7 == 0 else "low",
                    "account_age_days": rng.randint(1, 900),
                    "device_count": 1 + idx % 3,
                    "payment_instrument_count": 1 + idx % 2,
                    "merchant_diversity": 4 + idx % 16,
                    "legitimate_persona": personas[idx % len(personas)],
                    "fraud_ring_id": ring_members.get(account_id),
                }
                for idx, account_id in enumerate(account_ids)
            ),
        )
        handle.write(",")
        _write_fast_collection(
            handle,
            "payment_instruments",
            (
                {
                    "payment_instrument_id": f"pi_{account_id}_{pi}",
                    "account_id": account_id,
                    "instrument_type": ["card", "wallet"][pi % 2],
                    "issuer_region": regions[idx % len(regions)],
                    "created_day": -rng.randint(1, 700),
                    "active": True,
                }
                for idx, account_id in enumerate(account_ids)
                for pi in range(1 + idx % 2)
            ),
        )
        handle.write(",")
        _write_fast_collection(
            handle,
            "devices",
            (
                {
                    "device_id": f"dev_{account_id}_{device}",
                    "account_id": account_id,
                    "device_family": "consumer_device",
                    "first_seen_day": rng.randint(0, days - 1),
                    "synthetic_cluster_id": f"dev_cluster_{regions[idx % len(regions)]}",
                }
                for idx, account_id in enumerate(account_ids)
                for device in range(1 + idx % 3)
            ),
        )
        handle.write(",")
        _write_fast_collection(
            handle,
            "ip_clusters",
            (
                {
                    "ip_cluster_id": f"ip_{regions[idx % len(regions)]}_{idx:05d}",
                    "region": regions[idx % len(regions)],
                    "first_seen_day": rng.randint(0, days - 1),
                    "account_count": 1 + idx % 5,
                }
                for idx in range(max(1000, account_count // 2))
            ),
        )
        handle.write(",")
        _write_fast_collection(
            handle,
            "merchant_categories",
            (
                {
                    "category_id": f"cat_{category}",
                    "name": category,
                    "baseline_refund_rate": 0.08 if category in {"apparel", "marketplace"} else 0.03,
                    "baseline_chargeback_rate": 0.013 if category in {"digital_goods", "travel"} else 0.006,
                }
                for category in categories
            ),
        )
        handle.write(",")
        _write_fast_collection(
            handle,
            "merchants",
            (
                {
                    "merchant_id": merchant_id,
                    "category": categories[idx % len(categories)],
                    "region": regions[idx % len(regions)],
                    "normal_volume": float(5000 + idx * 137),
                    "refund_rate": 0.04 + (idx % 9) / 200,
                    "chargeback_rate": 0.004 + (idx % 5) / 1000,
                    "collusive_ring_id": None,
                }
                for idx, merchant_id in enumerate(merchant_ids)
            ),
        )
        handle.write(",")
        _write_fast_collection(handle, "rings", ring_rows)
        handle.write(",")
        handle.write('"transactions":[')
        for idx in range(transaction_count):
            if idx:
                handle.write(",")
            account_id = account_ids[idx % account_count]
            ring_id = ring_members.get(account_id)
            fraud = ring_id is not None and idx % 4 == 0
            merchant_id = merchant_ids[(idx * 17) % merchant_count]
            amount = round((18 + (idx % 900) * 1.17) * (1.8 if fraud else 1.0), 2)
            refunded = fraud and idx % 3 == 0 or (not fraud and idx % 41 == 0)
            chargeback = fraud and idx % 7 == 0 or (not fraud and idx % 211 == 0)
            tx = {
                "transaction_id": f"txn_{idx:08d}",
                "day": idx % days,
                "account_id": account_id,
                "merchant_id": merchant_id,
                "payment_instrument_id": f"pi_{account_id}_0",
                "device_id": f"dev_{account_id}_0",
                "ip_cluster_id": f"ip_{regions[idx % len(regions)]}_{idx % max(1000, account_count // 2):05d}",
                "amount": amount,
                "merchant_category": categories[idx % len(categories)],
                "region": regions[idx % len(regions)],
                "channel": ["web", "mobile", "in_app", "api"][idx % 4],
                "approved": idx % 29 != 0,
                "refunded": refunded,
                "chargeback": chargeback,
                "fraud_label": fraud,
                "ring_id": ring_id,
            }
            handle.write(json.dumps(tx, separators=(",", ":")))
            if refunded:
                refunds.append(
                    {
                        "refund_id": f"refund_{len(refunds):08d}",
                        "transaction_id": tx["transaction_id"],
                        "account_id": account_id,
                        "merchant_id": merchant_id,
                        "day": tx["day"] + 1,
                        "amount": round(amount * 0.55, 2),
                        "approved": tx["approved"],
                        "fraud_label": fraud,
                        "ring_id": ring_id,
                    }
                )
            if chargeback:
                chargebacks.append(
                    {
                        "chargeback_id": f"chargeback_{len(chargebacks):08d}",
                        "transaction_id": tx["transaction_id"],
                        "account_id": account_id,
                        "merchant_id": merchant_id,
                        "day": tx["day"] + 7,
                        "amount": amount,
                        "status": "lost" if fraud else "represented",
                        "fraud_label": fraud,
                        "ring_id": ring_id,
                    }
                )
        handle.write("],")
        for idx, chargeback in enumerate(chargebacks):
            disputes.append(
                {
                    "dispute_id": f"dispute_{idx:08d}",
                    "transaction_id": chargeback["transaction_id"],
                    "account_id": chargeback["account_id"],
                    "merchant_id": chargeback["merchant_id"],
                    "day": chargeback["day"],
                    "dispute_type": "chargeback",
                    "amount": chargeback["amount"],
                    "status": "open" if idx % 3 else "closed",
                    "fraud_label": chargeback["fraud_label"],
                    "ring_id": chargeback["ring_id"],
                }
            )
        for idx, refund in enumerate(refunds[: max(200, len(refunds) // 4)]):
            support_contacts.append(
                {
                    "support_contact_id": f"support_{idx:08d}",
                    "account_id": refund["account_id"],
                    "day": refund["day"],
                    "contact_type": "chat",
                    "topic": "refund_status",
                    "sentiment": "neutral",
                    "linked_transaction_id": refund["transaction_id"],
                }
            )
        for idx, account_id in enumerate(account_ids[::37]):
            account_changes.append(
                {
                    "account_change_id": f"acct_change_{idx:08d}",
                    "account_id": account_id,
                    "day": idx % days,
                    "change_type": "device_added",
                    "device_id": f"dev_{account_id}_0",
                    "ip_cluster_id": f"ip_{regions[idx % len(regions)]}_{idx % max(1000, account_count // 2):05d}",
                    "ring_id": ring_members.get(account_id),
                }
            )
        _write_fast_collection(handle, "refunds", refunds, leading_comma=False)
        handle.write(",")
        _write_fast_collection(handle, "chargebacks", chargebacks)
        handle.write(",")
        _write_fast_collection(handle, "disputes", disputes)
        handle.write(",")
        _write_fast_collection(handle, "support_contacts", support_contacts)
        handle.write(",")
        _write_fast_collection(handle, "account_changes", account_changes)
        handle.write("}")
    return {
        "path": str(out),
        "mode": "fast_stream",
        "accounts": account_count,
        "merchants": merchant_count,
        "transactions": transaction_count,
        "rings": ring_count,
        "refunds": len(refunds),
        "chargebacks": len(chargebacks),
        "disputes": len(disputes),
    }


def _write_fast_collection(handle, name: str, records, leading_comma: bool = False) -> None:
    if leading_comma:
        handle.write(",")
    handle.write(json.dumps(name))
    handle.write(":[")
    for idx, record in enumerate(records):
        if idx:
            handle.write(",")
        handle.write(json.dumps(record, separators=(",", ":")))
    handle.write("]")


if __name__ == "__main__":
    main()
