from appadmin.models import ProcessPackages

from pip._internal.operations.freeze import freeze

def update_dependencies():
    package_list = [{'package_name' :  x.split('==')[0]
                        ,'import_name' :  x.split('==')[0]
                        ,'current_version' :  x.split('==')[1]} for x in freeze()]
    
    for package in package_list:
        pp, created = ProcessPackages.objects.get_or_create(package_name=package['package_name'])
        if created:
            pp.import_name = package['import_name']
        pp.current_version = package['current_version']
        pp.save()
        print(package, created)