
def VideoDimsToResolutionDescription( iWidth, iHeight ):
    if ( iWidth == 0 or iHeight == 0 ):
        return ""
    elif ( iWidth <= 720 and iHeight <= 480 ):
        return "480"
    # 720x576 (PAL) (768 when rescaled for square pixels)
    elif ( iWidth <= 768 and iHeight <= 576 ):
        return "576"
    # 960x540 (sometimes 544 which is multiple of 16)
    elif ( iWidth <= 960 and iHeight <= 544 ):
        return "540"
    # 1280x720
    elif ( iWidth <= 1280 and iHeight <= 720 ):
        return "720"
    # 1920x1080
    else:
        return "1080"


def VideoAspectToAspectDescription( fAspect ):
    if ( fAspect == 0.0 ):
        return ""

    # Given that we're never going to be able to handle every single possibility in
    # aspect ratios, particularly when cropping prior to video encoding is taken into account
    # the best we can do is take the "common" aspect ratios, and return the closest one available.
    # The cutoffs are the geometric mean of the two aspect ratios either side.
    if ( fAspect < 1.4859 ): # sqrt(1.33*1.66)
        return "1.33"
    elif ( fAspect < 1.7190 ): # sqrt(1.66*1.78)
        return "1.66"
    elif ( fAspect < 1.8147 ): # sqrt(1.78*1.85)
        return "1.78"
    elif ( fAspect < 2.0174 ): # sqrt(1.85*2.20)
        return "1.85"
    elif ( fAspect < 2.2738 ): # sqrt(2.20*2.35)
        return "2.20"
    return "2.35"
