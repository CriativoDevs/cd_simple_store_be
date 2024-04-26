class DatabaseRouter:
    def db_for_read(self, model, **hints):
        # Route read operations to the appropriate database
        return getattr(model._meta, "db_alias", "default")

    def db_for_write(self, model, **hints):
        # Route write operations to the appropriate database
        return getattr(model._meta, "db_alias", "default")

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations between objects in different databases
        db1 = getattr(obj1._meta, "db_alias", "default")
        db2 = getattr(obj2._meta, "db_alias", "default")
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Allow migrations only for the appropriate database
        if db == "local":
            return False  # Don't migrate models for the local database
        return True
