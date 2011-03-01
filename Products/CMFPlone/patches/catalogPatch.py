from Products.ZCatalog.ZCatalog import ZCatalog

# Removing the docstring prevents these methods from being publishable.
del ZCatalog.getMetadataForRID.im_func.__doc__
del ZCatalog.getMetadataForUID.im_func.__doc__
del ZCatalog.getIndexDataForRID.im_func.__doc__
del ZCatalog.getIndexDataForUID.im_func.__doc__
del ZCatalog.getrid.im_func.__doc__
del ZCatalog.resolve_path.im_func.__doc__
