from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import *

class ContactSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="c_id", read_only=True)
    name = serializers.CharField(source="c_name", required=False)
    email = serializers.ListField(child=serializers.EmailField(), required=False, allow_null=True)
    phone = serializers.ListField(child=serializers.CharField(max_length=16), required=False, allow_null=True)

    class Meta:
        model = Contact
        fields = ["id", "name", "email", "phone"]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["email"] = [e.email for e in instance.emails.all()]
        ret["phone"] = [p.phone for p in instance.phones.all()]
        return ret

class LocationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="loc_id", read_only=True)
    name = serializers.CharField(source="loc_name", required=False)

    class Meta:
        model = Location
        fields = ["id", "name", "street", "city", "state", "zipcode"]

class ProgramSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="p_id", read_only=True)
    name = serializers.CharField(source="p_name")
    amount = serializers.FloatField(source="p_amount")
    location = LocationSerializer(source="locations", many=True, required=False)
    contact = ContactSerializer(source="contacts", many=True, required=False)

    class Meta:
        model = Program
        fields = ["id", "name", "age_min", "age_max", "amount", "duration", "location", "contact"]

class TagSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="t_id", read_only=True)
    name = serializers.CharField(source="t_name")

    class Meta:
        model = Tag
        fields = ["id", "name"]

# class BranchSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(source="b_id", read_only=True)
#     name = serializers.CharField(source="b_name")
#     location = LocationSerializer(source="locations", many=True)
#     program = ProgramSerializer(source="programs", many=True)
#     contact = ContactSerializer(source="contacts", many=True)
#
#     class Meta:
#         model = Branch
#         fields = ["id", "name", "location", "program", "contact"]

class MainSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="m_id", read_only=True)
    location = LocationSerializer(many=True, required=False)
    contact = ContactSerializer(many=True, required=False)

class VendorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="v_id", read_only=True)
    name = serializers.CharField(source="v_name")
    main = MainSerializer(required=False)
    program = ProgramSerializer(source="programs", many=True, required=False)

    class Meta:
        model = Vendor
        fields = ["id", "name", "domain", "has_sdp", "last_fetched", "main", "program"]

    # def validate_name(self, value):
    #     if Vendor.objects.filter(v_name__iexact=value).exists():
    #         raise serializers.ValidationError("Vendor with this name already exists")
    #     return value

    @transaction.atomic
    def create(self, validated_data):
        print(validated_data)
        main_data = validated_data.pop("main", None)
        program_data = validated_data.pop("programs", [])

        vendor, _ = Vendor.objects.update_or_create(
            domain=validated_data.get("domain"),
            defaults={
                "v_name": validated_data.get("v_name"),
                "has_sdp": validated_data.get("has_sdp"),
                "last_fetched": timezone.now()
            }
        )

        def sync_locations(locations_data, parent_kwargs):
            for location_data in locations_data:
                location_name = location_data.get("loc_name")
                Location.objects.update_or_create(
                    loc_name=location_name,
                    **parent_kwargs,
                    defaults={
                        "street": location_data.get("street"),
                        "city": location_data.get("city"),
                        "state": location_data.get("state"),
                        "zipcode": location_data.get("zipcode"),
                    }
                )

        def sync_contacts(contacts_data, parent_kwargs):
            for contact_data in contacts_data:
                emails = contact_data.pop("email", [])
                phones = contact_data.pop("phone", [])
                c_name = contact_data.pop("c_name")

                contact, _ = Contact.objects.update_or_create(
                    c_name=c_name,
                    **parent_kwargs,
                    defaults=contact_data
                )

                for email_str in emails:
                    Contact_Email.objects.create(contact=contact, email=email_str)

                for phone_str in phones:
                    Contact_Phone.objects.create(contact=contact, phone=phone_str)

        if main_data:
            sync_locations(main_data.get("location", []), {"v_id": vendor})
            sync_contacts(main_data.get("contact", []), {"v_id": vendor})

        for p_data in program_data:
            locations_data = p_data.pop("locations", [])
            contacts_data = p_data.pop("contacts", [])

            program, _ = Program.objects.update_or_create(
                v_id=vendor,
                p_name=p_data.get("p_name"),
                defaults=p_data
            )

            sync_locations(locations_data, {"p_id": program})
            sync_contacts(contacts_data, {"p_id": program})

        return vendor


    # @transaction.atomic
    # def create(self, validated_data):
    #     print(validated_data)
    #     main_data = validated_data.pop("main", None)
    #     program_data = validated_data.pop("programs", [])
    #
    #     vendor, created = Vendor.objects.update_or_create(
    #         domain=validated_data.get("domain"),
    #         defaults={
    #             "v_name": validated_data.get("v_name"),
    #             "has_sdp": validated_data.get("has_sdp"),
    #         }
    #     )
    #
    #     if not created:
    #         vendor.main_locations.all().delete()
    #         vendor.main_contacts.all().delete()
    #         vendor.programs.all().delete()
    #
    #     if main_data:
    #         locations_data = main_data.get("location", [])
    #         contacts_data = main_data.get("contact", [])
    #
    #         for location_data in locations_data:
    #             Location.objects.create(v_id=vendor, **location_data)
    #
    #         for contact_data in contacts_data:
    #             emails = contact_data.pop("email", [])
    #             phones = contact_data.pop("phone", [])
    #             contact = Contact.objects.create(v_id=vendor, **contact_data)
    #
    #             for email_str in emails:
    #                 Contact_Email.objects.create(contact=contact, email=email_str)
    #
    #             for phone_str in phones:
    #                 Contact_Phone.objects.create(contact=contact, phone=phone_str)
    #
    #     for p_data in program_data:
    #         locations_data = p_data.pop("locations", [])
    #         contacts_data = p_data.pop("contacts", [])
    #
    #         program = Program.objects.create(v_id=vendor, **p_data)
    #
    #         for location_data in locations_data:
    #             Location.objects.create(p_id=program, **location_data)
    #
    #         for contact_data in contacts_data:
    #             emails = contact_data.pop("email", [])
    #             phones = contact_data.pop("phone", [])
    #             contact = Contact.objects.create(p_id=program, **contact_data)
    #
    #             for email_str in emails:
    #                 Contact_Email.objects.create(contact=contact, email=email_str)
    #
    #             for phone_str in phones:
    #                 Contact_Phone.objects.create(contact=contact, phone=phone_str)
    #
    #     return vendor

class BatchCrawlInputSerializer(serializers.Serializer):
    vendor_url = serializers.URLField()
    vendor_programs = serializers.JSONField(required=False)