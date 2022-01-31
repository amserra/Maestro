from django.test import TestCase

"""
    Tests TODO:
    - Create organization, check if there is one member in membership and it is admin
    - Create organization, check if it can create contexts of that organization
    - Create organization, create a PUBLIC context within it and check if another user has access to it
    - Create organization, create a PRIVATE context within it and check that another user NOT in the organization has NOT access to it
    - Create organization, create a PRIVATE context within it and check that another user IN in the organization has NOT access to it
    - Leave organization NOT as an admin
    - Leave organization AS an admin with other admin existing
    - Leave organization AS an admin being the only existing admin (should provide warning: that will the entire organization) 
"""