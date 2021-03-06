from fontTools.pens.basePen import BasePen

from penTools import estimateCubicCurveLength, distance, interpolatePoint, getCubicPoint


class FlattenPen(BasePen):
    """
    This filter pen processes the contours into a series of straight lines by flattening the curves.

    - otherPen: a different segment pen object this filter should draw the results with.
    - approximateSegmentLength: the length you want the flattened segments to be (roughly).
    - segmentLines: whether to cut straight lines into segments as well.
    - filterDoubles: don't draw if a segment goes to the same coordinate.
    """

    def __init__(self, otherPen, approximateSegmentLength=5, segmentLines=False, filterDoubles=True):
        self.approximateSegmentLength = approximateSegmentLength
        BasePen.__init__(self, {})
        self.otherPen = otherPen
        self.currentPt = None
        self.firstPt = None
        self.segmentLines = segmentLines
        self.filterDoubles = filterDoubles

    def _moveTo(self, pt):
        self.otherPen.moveTo(pt)
        self.currentPt = pt
        self.firstPt = pt

    def _lineTo(self, pt):
        if self.filterDoubles:
            if pt == self.currentPt:
                return
        if not self.segmentLines:
            self.otherPen.lineTo(pt)
            self.currentPt = pt
            return
        d = distance(self.currentPt, pt)
        maxSteps = int(round(d / self.approximateSegmentLength))
        if maxSteps < 1:
            self.otherPen.lineTo(pt)
            self.currentPt = pt
            return
        step = 1.0 / maxSteps
        factors = range(0, maxSteps + 1)
        for i in factors[1:]:
            self.otherPen.lineTo(interpolatePoint(self.currentPt, pt, i * step))
        self.currentPt = pt

    def _curveToOne(self, pt1, pt2, pt3):
        est = estimateCubicCurveLength(self.currentPt, pt1, pt2, pt3) / self.approximateSegmentLength
        maxSteps = int(round(est))
        falseCurve = (pt1 == self.currentPt) and (pt2 == pt3)
        if maxSteps < 1 or falseCurve:
            self.otherPen.lineTo(pt3)
            self.currentPt = pt3
            return
        step = 1.0 / maxSteps
        factors = range(0, maxSteps + 1)
        for i in factors[1:]:
            pt = getCubicPoint(i * step, self.currentPt, pt1, pt2, pt3)
            self.otherPen.lineTo(pt)
        self.currentPt = pt3

    def _closePath(self):
        self.lineTo(self.firstPt)
        self.otherPen.closePath()
        self.currentPt = None

    def _endPath(self):
        self.otherPen.endPath()
        self.currentPt = None

    def addComponent(self, glyphName, transformation):
        self.otherPen.addComponent(glyphName, transformation)


def flattenGlyph(aGlyph, threshold=10, segmentLines=True):
    """
    Convenience function that applies the **FlattenPen** pen to a glyph. Returns a new glyph object.
    """
    if len(aGlyph) == 0:
        return aGlyph
    from ufoLib.pointPen import SegmentToPointPen
    from fontPens.dataPointPen import DataPointPen
    data = DataPointPen()
    filterpen = FlattenPen(SegmentToPointPen(data), approximateSegmentLength=threshold, segmentLines=segmentLines)
    aGlyph.draw(filterpen)
    aGlyph.clear()
    data.draw(aGlyph.getPen())
    return aGlyph


# =========
# = tests =
# =========

def _makeTestGlyph():
    # make a simple glyph that we can test the pens with.
    from fontParts.nonelab import RGlyph
    testGlyph = RGlyph()
    testGlyph.name = "testGlyph"
    testGlyph.width = 500
    pen = testGlyph.getPen()
    pen.moveTo((10, 10))
    pen.lineTo((10, 30))
    pen.lineTo((30, 30))
    pen.lineTo((30, 10))
    pen.closePath()
    return testGlyph


def _testFlattenPen():
    """
    >>> from printPen import PrintPen
    >>> glyph = _makeTestGlyph()
    >>> pen = FlattenPen(PrintPen(), approximateSegmentLength=10, segmentLines=True)
    >>> glyph.draw(pen)
    pen.moveTo((10, 10))
    pen.lineTo((10.0, 20.0))
    pen.lineTo((10.0, 30.0))
    pen.lineTo((20.0, 30.0))
    pen.lineTo((30.0, 30.0))
    pen.lineTo((30.0, 20.0))
    pen.lineTo((30.0, 10.0))
    pen.lineTo((20.0, 10.0))
    pen.lineTo((10.0, 10.0))
    pen.closePath()
    """


def _testFlattenGlyph():
    """
    >>> from printPen import PrintPen
    >>> glyph = _makeTestGlyph()
    >>> glyph = flattenGlyph(glyph)
    >>> glyph.draw(PrintPen())
    pen.moveTo((10.0, 10.0))
    pen.lineTo((10.0, 20.0))
    pen.lineTo((10.0, 30.0))
    pen.lineTo((20.0, 30.0))
    pen.lineTo((30.0, 30.0))
    pen.lineTo((30.0, 20.0))
    pen.lineTo((30.0, 10.0))
    pen.lineTo((20.0, 10.0))
    pen.closePath()
    """


if __name__ == "__main__":
    import doctest
    doctest.testmod()
