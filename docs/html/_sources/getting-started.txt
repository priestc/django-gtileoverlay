.. highlight:: python

Getting started with django-gtileoverlay
----------------------------------------

1. First, make a URL pattern::

.. code-block:: python

    (r'^overlay/(?P<z>\d{1,2})_(?P<x>\d{1,5})_(?P<y>\d{1,5}).png$', 'my_app.views.overlay'),
    # matches all requests that look like this: http://domain.com/overlay/23_34_54.png
    
2. Now create a view like so::

.. code-block:: python

    def overlay(request, z, x, y):
        from overlay.overlays import GTileOverlay as GTO
        
        qs = MyModel.objects.all()
        qs2 = MyOtherModel.objects.all() 
        
        ov = GTO(z,x,y,
                 queryset=qs,
                 field='location',  # Name of the PointField which contains the lat/long information
                 icon="/path/to/icon.png")    
                         
        ov2 = GTO(z,x,y,
                  queryset=qs2,
                  fields=('lat', 'lng'), # name of the two FloatFields containing the lat/longs
                  hard_limit=500,        # limit the amount of icons per square to 500 items.
                  image=ov.output(),     # output overtop the previous overlay
                 )
                 
        response = HttpResponse(mimetype="image/png")
        ov2.output().save(response, "PNG")
        return response
       
3. Finally, add the following code to your google maps page::

.. code-block:: html

    <script type="text/javascript">
          var MyOverlay = new GTileLayerOverlay(
               new GTileLayer(null, null, null, {
                  tileUrlTemplate: '/overlay/{Z}_{X}_{Y}.png/',     //must match your urlpattern
                  isPng:true,
                  opacity:1.0}
               )
          );
          map.addOverlay(MyOverlay);
    </script>
