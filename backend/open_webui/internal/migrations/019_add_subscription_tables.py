"""Peewee migrations -- 019_add_subscription_tables.py.

Some examples (model - class or model name)::

    > Model = migrator.orm['table_name']            # Return model in current state by name
    > Model = migrator.ModelClass                   # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python function with the given args
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.add_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)
    > migrator.add_constraint(model, name, sql)
    > migrator.drop_index(model, *col_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.drop_constraints(model, *constraints)

"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class SubscriptionPlan(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        plan_name = pw.CharField(max_length=255)
        subtitle = pw.TextField(null=True)
        plan_type = pw.CharField(max_length=255, default="premium")
        duration_type = pw.CharField(max_length=255, default="months")
        plan_duration = pw.BigIntegerField(default=1)
        price = pw.FloatField()
        benefits = pw.TextField(null=True)  # JSON stored as text
        additional_info = pw.TextField(null=True)
        group = pw.CharField(max_length=255, null=True)
        models = pw.TextField(null=True)  # JSON stored as text
        users = pw.TextField(null=True)  # JSON stored as text
        is_active = pw.BooleanField(default=True)
        created_at = pw.BigIntegerField()
        updated_at = pw.BigIntegerField()

        class Meta:
            table_name = "subscription_plan"

    @migrator.create_model
    class UserSubscription(pw.Model):
        id = pw.CharField(max_length=255, primary_key=True)
        user_id = pw.CharField(max_length=255)
        plan_id = pw.CharField(max_length=255)
        status = pw.CharField(max_length=255, default="pending")
        payment_id = pw.CharField(max_length=255, null=True)
        payment_method = pw.CharField(max_length=255, null=True)
        start_date = pw.BigIntegerField(null=True)
        end_date = pw.BigIntegerField(null=True)
        auto_renew = pw.BooleanField(default=True)
        created_at = pw.BigIntegerField()
        updated_at = pw.BigIntegerField()

        class Meta:
            table_name = "user_subscription"

    # Add indexes
    migrator.add_index("subscription_plan", "is_active")
    migrator.add_index("subscription_plan", "plan_type")
    migrator.add_index("user_subscription", "user_id")
    migrator.add_index("user_subscription", "plan_id")
    migrator.add_index("user_subscription", "status")
    migrator.add_index("user_subscription", "end_date")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    # Drop indexes first
    migrator.drop_index("user_subscription", "end_date")
    migrator.drop_index("user_subscription", "status")
    migrator.drop_index("user_subscription", "plan_id")
    migrator.drop_index("user_subscription", "user_id")
    migrator.drop_index("subscription_plan", "plan_type")
    migrator.drop_index("subscription_plan", "is_active")

    # Drop tables
    migrator.remove_model("user_subscription")
    migrator.remove_model("subscription_plan")
