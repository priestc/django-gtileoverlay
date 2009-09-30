.. highlight:: python

Additional Features
-------------------

==================================================
Filtering a queryset instead of returning an image
==================================================

Instead of producing an image, you can have GTileOverlay return the queryset
filtered by the X and Y tile coordinates::

    >>> qs = Model.objects.all()
    >>> ov = GTileOverlay(5, 45, 15, queryset=qs)
    >>> new_qs = ov.output(just_queryset=True)

or this way::

    >>> qs = Model.objects.all()
    >>> ov = GTileOverlay(5, 45, 15, queryset=qs, field="location")
    >>> kwargs = ov.get_filter()
    >>> kwargs
    {'location__intersects': 'POLYGON((0.0 -89.998077637,0.0 -89.9907525165,90.0 -89.9907525165,90.0 -89.998077637,0.0 -89.998077637))'}
    >>> new_qs = qs.filter(**kwargs)
    
=================================
Expanding the filter bounding box
=================================

If the queryset is filtered by the exact bounds of the lattitude and longitude
coordinates of the image, then there will issues where some icons will be
cut off. It order to fix this problem, ``GTileOverlay.get_filter()`` method
tries to expand the query filter bounds by a small amount, allowing points
just beyond the bounds to be plotted on that image.

If an icon falls a few pixels from the edge of two tiles, both tiles will drawl
that point. One tile prints one half of the icon, the other tile prints the
other half.

One side effect of this method is that if you want to get the absolute number
of points that fall within a tile, you must not rely on the queryset that
was filtered with the expanded filter. Doing so will return a number larger
than expected since points near the edges are being returned more than once.
