import Image
import ImageFont
import ImageDraw
import random

from django.contrib.gis.gdal.envelope import Envelope

from globalmaptiles import GlobalMercator

class GTileOverlay():
    """Creates a 256*256 PNG image with overlayed markers for use on
    GTileOverlay layers in Google Maps.
    
    .. tabularcolumns:: |l|L|

    ==============   ====================================================
    Keyword          Description
    ==============   ====================================================
    zoom             Zoom level of the Google Map (should be set
                     automatically by the Google Maps API)
    x, y             X and Y coordinates of the tile image.
    image            The starting image that will get printed to
    queryset         The queryset that will be filtered down to the
                     lat/long bounds
    hard_limit       Maximum number of points that will be printed on each
                     image
    icon             Path to the icon that will be used to denote each
                     location
    fields           The name of the lat/long fields in the model. Must be
                     ``FloatField``s
    field            The same as **fields** except a single ``PointField``
                     (part of GeoDjango) instead of ``FloatField``           
    ==============   ====================================================
    """
    gm = GlobalMercator()
    double_field_name = None
    single_field_name = None
    icon = None
    icon_width = None
    queryset = None

    def __init__(self, zoom, x, y, image=None, queryset=None, hard_limit=None,
                 icon=None, field=None, fields=None):

        self.hard_limit = hard_limit
        
        try:
            self.zoom = int(zoom)
        except TypeError:
            raise TypeError, "Zoom must be an integer"
        
        #convert google XY image blocks to some other kind of image block format
        self.ox, self.oy = self.gm.GoogleTile(int(x),int(y),self.zoom)
        
        #convert this other image block format into lat/lng bound values
        self.N, self.W, self.S, self.E = self.gm.TileLatLonBounds(self.ox,
                                                            self.oy, self.zoom) 
        if queryset:
            self.queryset = queryset

        if icon:
            self.icon(icon)

        if not image:
            self.im = Image.new("RGBA", (256,256))
        else:
            self.im = image

        if field:
            self.single_field_name = field

        elif fields:
            self.double_field_name = fields

        # save google's x and y coordinate values for debugging
        self.gx, self.gy = x, y



    def icon(self, path):
        """sets the icon, and automatically sets the width of the icon.
        """
        self.icon = Image.open(path)
        self.icon_width = self.icon.getbbox()[2]
        return self.icon_width

    def _expand(self):
        """Extends the bounds by half the width of the icon used so any icons
        that are placed near the edges of any image will not get cut off.
        This can't be called until an icon has been set.
        """

        if not self.icon_width:
            raise ValueError,\
        "Can't expand filter if no icon is set, instead try 'expand=False'"

        #number of meters in one pixel.
        res = self.gm.Resolution(self.zoom) 
        
        #number of meters for half an icon.          
        rev = res * self.icon_width / 2
                   
        #expantion in lat and long degrees.
        e_lat, e_long = self.gm.MetersToLatLon(rev, rev)

        return e_lat, e_long

    def get_filter(self, expand=True):
        """Creates a filter with the bounds being the lattitude/longitude of
        the image. expand=True will expand the bounds one half the icon's
        width. An icon mut be set for this feature to work
        """

        if expand and not self.icon:
            raise ValueError, "Can't expand unless an icon is set"
        
        elif expand and self.icon:
            e_lat, e_long = self._expand()  #get the offset
            
        else:
            e_lat, e_long = 0,0  # no offset

        # add the offset to each side of the bounding box
        ex_W = self.W - e_lat
        ex_E = self.E + e_lat
        ex_S = self.S + e_long
        ex_N = self.N - e_long

        if self.single_field_name:  # using GeoDjango PointField
            bounds = Envelope( (ex_W, ex_N, ex_E, ex_S) )
            arg = { self.single_field_name + "__intersects": str(bounds.wkt) }

        elif self.double_field_name:    # Using two FloatFields
            lat = self.double_field_name[0]
            lng = self.double_field_name[1]

            arg = { lat + "__lte": ex_N,
                    lat + "__gte": ex_S,
                    lng + "__lte": ex_E,
                    lng + "__gte": ex_W,
                  }
        else:
            raise ValueError, "No location field specified"
            
        return arg

    def _shuffle(self):
        """Shuffles the points so they are rendered in no particular order,
        helps to minimize odd overlapping effects"""

        self.queryset = self.queryset.order_by('?')

    def _put_points(self):
        """Evaluates the queryset, goes through each point, calculates the
        correct coordinate for PIL, and then places the points onto the image
        """

        for base in self.geobases:

            if self.single_field_name:
                lat = getattr(base, self.single_field_name).y
                lng = getattr(base, self.single_field_name).x
            else:
                lat = getattr(base, self.single_field_name[0])
                lng = getattr(base, self.single_field_name[1])
                
            #meters from (0,0) to the point
            meters = self.gm.LatLonToMeters(lat,lng)
            
            #pixels from (0,0) to the point
            pixs = self.gm.MetersToPixels(meters[0], meters[1], self.zoom)
            #pixels within this 256x256 image
            tx = pixs[0] - (256 * self.ox)
            ty = pixs[1] - (256 * self.oy)

            fx = tx
            fy = 256-ty
            
            #adjust so the icon is at the center of the point
            x = int(fx - (self.icon_width / 2))
            y = int(fy - (self.icon_width / 2))

            self.im.paste(self.icon, (x, y), self.icon)

    def output(self, debug=False, expand=True, just_queryset=False,
                     shuffle=False):
        """All points are placed on the image, and then that image is returned.
        Instead of calling this function, you can also call `as_response()`
        with the same arguments, which will return the image as a django
        response object.
        
            .. tabularcolumns:: |l|L|

        ==============   ====================================================
        Keyword          Description
        ==============   ====================================================
        debug            If set to True, some debug information will be
                         outputted to the image, and a red box will be printed
                         around each image.
        expand           If set to false, the queryset bounding filter will not
                         be expanded, so any icons placed near the edge of the
                         image will get cut-off. Useful for getting the exact
                         number of items that are in the bounding box.
        shuffle          If set to False, the queryset will not be shuffled.
                         Shuffling occurs by adding ".order_by('?')" to the end
                         of the queryset. This helps minimize odd overlapping
                         effects that occur sometimes. Different databases
                         handle this shuffling technique, so it can be a
                         performance issue.
        just_queryset    If set to True, returns just the queryset of object
                         without placing them into the image.
        ==============   ====================================================
        
        """
                    
        #if queryset is empty or no icon is set, return original image
        if (not self.queryset or not self.icon_width) and not just_queryset:
            if debug:
                self.geobases = "empty"
                self.queryset = "empty"
                self.debug_messages()
            return self.im

        if shuffle:
            self._shuffle()

        kwargs = self.get_filter(expand=expand)
        self.geobases = self.queryset.filter(**kwargs)
        
        if self.hard_limit:
            self.geobases = self.geobases[:self.hard_limit]

        if just_queryset:
            return self.geobases

        if debug:
            self._debug_messages()

        # if there are no geobases, just return the unmodified original image
        if self.geobases.count() < 1:
            return self.im

        self._put_points()

        return self.im

    def as_response(self, *args, **kwargs):
        """
        Returns the image as a django response object
        """
        
        from django.http import HttpResponse
        response = HttpResponse(mimetype="image/png")
        self.output(*args, **kwargs).save(response, "PNG")
        
        return response

    def _debug_messages(self):
        """Prints debug messages and a red bounding box onto the outputted
        image
        """

        font = ImageFont.load_default()
        draw = ImageDraw.Draw(self.im)

        draw.line( [(0,0),(0,255)], fill='red', width=1)
        draw.line( [(0,255),(255,255)], fill='red', width=1)

        draw.text((10, 150), "zoom=" + str(self.zoom) + " x=" + str(self.gx) +
                                ", y=" + str(self.gy), font=font, fill='black')
        draw.text((10, 230), "inside= " + str(self.geobases.count()),
                                font=font, fill='black')
        draw.text((10, 210), "total = " + str(self.queryset.count()),
                                font=font, fill='black')
