from django.db import models

class Vendor(models.Model):
    v_id = models.AutoField(primary_key=True)
    v_name = models.CharField(max_length=256)
    domain = models.URLField()
    has_sdp = models.BooleanField(default=False)
    last_fetched = models.DateTimeField(auto_now_add=True)

    @property
    def main(self):
        return {
            "location": self.main_locations.all(),
            "contact": self.main_contacts.all()
        }

    def __str__(self):
        return self.v_name

# class Branch(models.Model):
#     b_id = models.AutoField(primary_key=True)
#     b_name = models.CharField(max_length=256)
#     v_id = models.OneToOneField(Vendor, on_delete=models.CASCADE, db_column="v_id")
#
#     def __str__(self):
#         return self.b_name

# class Main(models.Model):
#     m_id = models.AutoField(primary_key=True)
#     v_id = models.OneToOneField(Vendor, related_name="main", on_delete=models.CASCADE, db_column="v_id")
#
#     def __str__(self):
#         return self.m_id

class Program(models.Model):
    p_id = models.AutoField(primary_key=True)
    v_id = models.ForeignKey(Vendor, related_name="programs", on_delete=models.CASCADE, db_column="v_id")
    p_name = models.CharField(max_length=256)
    age_min = models.IntegerField(null=True)
    age_max = models.IntegerField(null=True)
    p_amount = models.FloatField(default=0.0)
    duration = models.FloatField(default=0.0)

    def __str__(self):
        return self.p_name

class Contact(models.Model):
    c_id = models.AutoField(primary_key=True)
    v_id = models.ForeignKey(Vendor, related_name="main_contacts", null=True, on_delete=models.CASCADE, db_column="v_id")
    p_id = models.ForeignKey(Program, related_name="contacts", null=True, on_delete=models.CASCADE, db_column="p_id")
    c_name = models.CharField(max_length=256, null=True)

    def __str__(self):
        return self.c_name

class Contact_Email(models.Model):
    contact = models.ForeignKey(Contact, related_name="emails", on_delete=models.CASCADE, db_column="c_id")
    email = models.EmailField()

    def __str__(self):
        return self.email

class Contact_Phone(models.Model):
    contact = models.ForeignKey(Contact, related_name="phones", on_delete=models.CASCADE, db_column="c_id")
    phone = models.CharField(max_length=16)

    def __str__(self):
        return self.phone

class Location(models.Model):
    loc_id = models.AutoField(primary_key=True)
    v_id = models.ForeignKey(Vendor, related_name="main_locations", null=True, on_delete=models.CASCADE, db_column="v_id")
    p_id = models.ForeignKey(Program, related_name="locations", null=True, on_delete=models.CASCADE, db_column="p_id")
    loc_name = models.CharField(max_length=256, null=True)
    street = models.CharField(max_length=256)
    city = models.CharField(max_length=256)
    state = models.CharField(max_length=256)
    zipcode = models.CharField(max_length=256)

    def __str__(self):
        return self.loc_name

class Tag(models.Model):
    t_id = models.AutoField(primary_key=True)
    t_name = models.CharField(max_length=256)

    def __str__(self):
        return self.t_name
