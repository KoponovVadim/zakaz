from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.crypto import encrypt_secret, generate_secret, hash_secret
from app.db.session import SessionLocal
from app.models import Client, Order, OrderItem, Site, SiteSource


def main() -> None:
    with SessionLocal() as db:
        client = db.scalar(select(Client).where(Client.name == "Demo Client"))
        if not client:
            client = Client(name="Demo Client", comment="Тестовый клиент для проверки заказов")
            db.add(client)
            db.flush()

        site = db.scalar(select(Site).where(Site.normalized_url == "https://demo.example.ru"))
        if not site:
            secret = generate_secret()
            site = Site(
                client_id=client.id,
                name="Demo Joomla Shop",
                url="https://demo.example.ru",
                normalized_url="https://demo.example.ru",
                joomla_version="4",
                site_uid="demo-site-uid",
                connector_secret_encrypted=encrypt_secret(secret),
                connector_secret_hash=hash_secret(secret),
                connector_version=settings.connector_version,
                status="active",
            )
            site.sources.append(SiteSource(source_type="rsform", is_enabled=True, discovered=True))
            site.sources.append(SiteSource(source_type="virtuemart", is_enabled=True, discovered=True))
            db.add(site)
            db.flush()

        rsform_order = db.scalar(
            select(Order).where(
                Order.site_id == site.id,
                Order.source_type == "rsform",
                Order.external_id == "demo-rsform-1",
            )
        )
        if not rsform_order:
            db.add(
                Order(
                    client_id=client.id,
                    site_id=site.id,
                    source_type="rsform",
                    external_id="demo-rsform-1",
                    external_number="RS-1001",
                    customer_name="Иван Петров",
                    customer_phone="+7 900 000-00-01",
                    customer_email="ivan@example.ru",
                    title="Заявка с формы",
                    message="Нужна консультация по проекту.",
                    external_status="submitted",
                    internal_status="new",
                    raw_payload={"demo": True, "source": "rsform"},
                )
            )

        vm_order = db.scalar(
            select(Order).where(
                Order.site_id == site.id,
                Order.source_type == "virtuemart",
                Order.external_id == "demo-vm-1",
            )
        )
        if not vm_order:
            vm_order = Order(
                client_id=client.id,
                site_id=site.id,
                source_type="virtuemart",
                external_id="demo-vm-1",
                external_number="VM-2001",
                customer_name="Анна Смирнова",
                customer_phone="+7 900 000-00-02",
                customer_email="anna@example.ru",
                title="Заказ VirtueMart",
                amount=Decimal("12990.00"),
                currency="RUB",
                external_status="confirmed",
                internal_status="in_progress",
                raw_payload={"demo": True, "source": "virtuemart"},
            )
            vm_order.items.append(OrderItem(sku="SKU-1", name="Разработка лендинга", quantity=Decimal("1"), price=Decimal("12990.00")))
            db.add(vm_order)

        db.commit()
        print("Demo orders are ready")


if __name__ == "__main__":
    main()
