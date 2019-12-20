from django.db import models


class ProcessPackages(models.Model):
    package_name = models.CharField(max_length=100)
    import_name = models.CharField(max_length=100)
    common_short_hand = models.CharField(max_length=100, null=True, blank=True)
    current_version = models.CharField(max_length=100, null=True, blank=True)

    is_base_package = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['package_name']
        db_table = 'appadmin_packages'
        verbose_name = 'Package'
        verbose_name_plural = 'Packages'

    @property
    def package_display(self):
        if self.current_version:
            return '{}=={}'.format(self.package_name, self.current_version)
        else:
            return self.package_name

    def __str__(self):
        if self.common_short_hand is None:
            return str(self.package_name)
        else:
            return '{} as {}'.format(str(self.package_name), str(self.common_short_hand))