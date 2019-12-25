from datetime import datetime
from fontTools import ttLib
from fontTools.cffLib import (
    TopDictIndex,
    TopDict,
    CharStrings,
    SubrsIndex,
    GlobalSubrsIndex,
    PrivateDict,
    IndexedStrings,
)
from fontTools.misc.fixedTools import otRound
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4, cmap_format_12
from fontTools.ttLib.tables.O_S_2f_2 import Panose
from tfont2ft import conversion, drawing, semlog
from tfont2ft.fontdata import FontData, FontProc
from tfont2ft.types import Context


def otRoundSequence(iterable):
    return list(map(otRound, iterable))


class BaseFontCompiler:
    sfntVersion = NotImplemented

    # currently we only compile a given master
    def __init__(self, font, mastername=None):
        if mastername is None:
            master = font.selectedMaster
        else:
            master = font.masterForName(mastername)
        self.ctx = Context(font, master)
        self.metadataProvider = FontData

    def compile(self):
        self.otf = ttLib.TTFont(sfntVersion=self.sfntVersion)
        self.build_requirements()

        self.otf.setGlyphOrder(self.glyphOrder)

        self.build_head()
        self.build_hmtx()
        self.build_hhea()
        self.build_name()
        self.build_maxp()
        self.build_cmap()
        self.build_OS2()
        self.build_post()

        # TODO: GPOS, GSUB

        self.build_others()

        return (self.otf, self.ctx.log)

    ##

    def build_requirements(self):
        ctx = self.ctx
        self.glyphMap, self.glyphOrder = FontProc.production_glyphs(ctx)
        self.fontBounds, self.glyphBoundsMap = FontProc.font_glyph_bounds(ctx, self.glyphMap)
        self.unicodeToGlyphNameMap = FontProc.unicode_glyphname_map(ctx, self.glyphMap)

    def build_cmap(self):
        self.otf["cmap"] = cmap = ttLib.newTable("cmap")
        cmap.tableVersion = 0

        nonBMP = dict(
            (k, v) for k, v in self.unicodeToGlyphNameMap.items() if k > 65535
        )
        if nonBMP:
            mapping = dict(
                (k, v) for k, v in self.unicodeToGlyphNameMap.items() if k <= 65535
            )
        else:
            mapping = dict(self.unicodeToGlyphNameMap)

        # mac
        cmap4_0_3 = cmap_format_4(4)
        cmap4_0_3.platformID = 0
        cmap4_0_3.platEncID = 3
        cmap4_0_3.language = 0
        cmap4_0_3.cmap = mapping
        # windows
        cmap4_3_1 = cmap_format_4(4)
        cmap4_3_1.platformID = 3
        cmap4_3_1.platEncID = 1
        cmap4_3_1.language = 0
        cmap4_3_1.cmap = mapping
        cmap.tables = [cmap4_0_3, cmap4_3_1]

        if nonBMP:
            nonBMP.update(mapping)

            # mac
            cmap12_0_4 = cmap_format_12(12)
            cmap12_0_4.platformID = 0
            cmap12_0_4.platEncID = 4
            cmap12_0_4.language = 0
            cmap12_0_4.cmap = nonBMP
            # windows
            cmap12_3_10 = cmap_format_12(12)
            cmap12_3_10.platformID = 3
            cmap12_3_10.platEncID = 10
            cmap12_3_10.language = 0
            cmap12_3_10.cmap = nonBMP

            cmap.tables = [cmap4_0_3, cmap4_3_1, cmap12_0_4, cmap12_3_10]

    def build_head(self):
        ctx = self.ctx
        data = self.metadataProvider
        self.otf["head"] = head = ttLib.newTable("head")
        head.checkSumAdjustment = 0
        head.tableVersion = 1.0
        head.magicNumber = 0x5F0F3CF5

        head.fontRevision = data.head_version(ctx)
        head.unitsPerEm = otRound(data.unitsPerEm(ctx))

        head.created = conversion.to_opentype_timestamp(data.date(ctx))
        head.modified = conversion.to_opentype_timestamp(datetime.utcnow())

        fontBounds = self.fontBounds
        if fontBounds.empty:
            head.xMin = head.yMin = head.xMax = head.yMax = 0
        else:
            head.xMin = otRound(fontBounds.left)
            head.yMin = otRound(fontBounds.bottom)
            head.xMax = otRound(fontBounds.right)
            head.yMax = otRound(fontBounds.top)

        head.macStyle = data.head_macStyle(ctx)

        head.flags = 0x3
        head.lowestRecPPEM = 6
        head.fontDirectionHint = 2
        head.indexToLocFormat = 0
        head.glyphDataFormat = 0

    def build_hhea(self):
        ctx = self.ctx
        hmtx = self.otf.get("hmtx")
        data = self.metadataProvider
        self.otf["hhea"] = hhea = ttLib.newTable("hhea")
        hhea.tableVersion = 0x00010000

        hhea.ascender, \
        hhea.descender, \
        hhea.lineGap = otRoundSequence(data.hhea_metrics(ctx))
        hhea.caretSlopeRise, \
        hhea.caretSlopeRun, \
        hhea.caretOffset = otRoundSequence(data.hhea_caretMetrics(ctx))

        # Horizontal metrics
        advances = []  # width in hhea
        firstSideBearings = []  # left in hhea
        secondSideBearings = []  # right in hhea
        extents = []

        if hmtx is not None:
            for glyphName in self.glyphOrder:
                advance, firstSideBearing = hmtx[glyphName]
                advances.append(advance)
                bounds = self.glyphBoundsMap[glyphName]
                if bounds is not None:
                    boundsAdvance = bounds.right - bounds.left
                    # equation from the hhea spec for calculating xMaxExtent:
                    #   Max(lsb + (xMax - xMin))
                    extent = firstSideBearing + boundsAdvance
                    secondSideBearing = advance - firstSideBearing - boundsAdvance

                    firstSideBearings.append(firstSideBearing)
                    secondSideBearings.append(secondSideBearing)
                    extents.append(extent)
        else:
            ctx.log.append(
                semlog.warning_missing_hmtx(target="hhea")
            )

        hhea.advanceWidthMax = max(advances) if advances else 0
        hhea.minLeftSideBearing = min(firstSideBearings) if firstSideBearings else 0
        hhea.minRightSideBearing = min(secondSideBearings) if secondSideBearings else 0
        hhea.xMaxExtent = max(extents) if extents else 0

        hhea.reserved0 = hhea.reserved1 = hhea.reserved2 = hhea.reserved3 = 0
        hhea.metricDataFormat = 0
        hhea.numberOfHMetrics = len(self.glyphOrder)

    def build_hmtx(self):
        ctx = self.ctx
        data = self.metadataProvider
        self.otf["hmtx"] = hmtx = ttLib.newTable("hmtx")
        hmtx.metrics = {}

        for glyphName, glyph in self.glyphMap.items():
            width = otRound(data.glyph_width(ctx, glyph))
            bounds = self.glyphBoundsMap[glyphName]
            left = otRound(bounds.left) if not bounds.empty else 0

            hmtx[glyphName] = (width, left)

    def build_maxp(self):
        raise NotImplementedError

    def build_name(self):
        ctx = self.ctx
        data = self.metadataProvider
        self.otf["name"] = name = ttLib.newTable("name")
        name.names = []

        familyName = data.stylemap_familyName(ctx)
        styleName = data.stylemap_styleName(ctx).title()

        nameVals = {
            0: data.copyright(ctx),
            1: familyName,
            2: styleName,
            3: data.name_uniqueID(ctx),
            4: data.name_postscriptFullName(ctx),
            5: data.name_version(ctx),
            6: data.name_postscriptFontName(ctx),
            7: data.name_trademark(ctx),
            8: data.manufacturer(ctx),
            9: data.designer(ctx),
            10: data.name_description(ctx),
            11: data.manufacturerURL(ctx),
            12: data.designerURL(ctx),
            13: data.name_license(ctx),
            14: data.name_licenseURL(ctx),
            16: data.name_preferredFamilyName(ctx),
            17: data.name_preferredSubfamilyName(ctx),
        }

        # don't add typographic names if they are the same as the legacy ones
        if nameVals[1] == nameVals[16]:
            del nameVals[16]
        if nameVals[2] == nameVals[17]:
            del nameVals[17]

        for nameId in nameVals.keys():
            nameVal = nameVals[nameId]
            if nameVal:
                platformId = 3
                platEncId = 10 if FontProc.is_non_bmp(nameVal) else 1
                langId = 0x409
                name.setName(nameVal, nameId, platformId, platEncId, langId)

    def build_OS2(self):
        ctx = self.ctx
        data = self.metadataProvider
        self.otf["OS/2"] = os2 = ttLib.newTable("OS/2")
        os2.version = 0x0004
        os2.xAvgCharWidth = FontProc.average_char_width(ctx, self.otf)

        os2.usWeightClass = data.OS2_weightClass(ctx)
        os2.usWidthClass = data.OS2_widthClass(ctx)

        os2.fsType = data.OS2_fsType(ctx)

        os2.ySubscriptXSize = otRound(data.OS2_subscriptXSize(ctx))
        os2.ySubscriptYSize = otRound(data.OS2_subscriptYSize(ctx))
        os2.ySubscriptXOffset = otRound(data.OS2_subscriptXOffset(ctx))
        os2.ySubscriptYOffset = otRound(data.OS2_subscriptYOffset(ctx))

        os2.ySuperscriptXSize = otRound(data.OS2_superscriptXSize(ctx))
        os2.ySuperscriptYSize = otRound(data.OS2_superscriptYSize(ctx))
        os2.ySuperscriptXOffset = otRound(data.OS2_superscriptXOffset(ctx))
        os2.ySuperscriptYOffset = otRound(data.OS2_superscriptYOffset(ctx))

        os2.yStrikeoutSize = otRound(data.OS2_strikeoutSize(ctx))
        os2.yStrikeoutPosition = otRound(data.OS2_strikeoutPosition(ctx))

        os2.sFamilyClass = data.OS2_familyClass(ctx)

        panose = Panose()
        panose.bFamilyType, \
        panose.bSerifStyle, \
        panose.bWeight, \
        panose.bProportion, \
        panose.bContrast, \
        panose.bStrokeVariation, \
        panose.bArmStyle, \
        panose.bLetterForm, \
        panose.bMidline, \
        panose.bXHeight = data.OS2_panose(ctx)
        os2.panose = panose

        unicodeRanges = data.OS2_unicodeRanges(ctx)
        if unicodeRanges is not None:
            os2.ulUnicodeRange1 = conversion.to_bitflags(unicodeRanges, 0, 32)
            os2.ulUnicodeRange2 = conversion.to_bitflags(unicodeRanges, 32, 32)
            os2.ulUnicodeRange3 = conversion.to_bitflags(unicodeRanges, 64, 32)
            os2.ulUnicodeRange4 = conversion.to_bitflags(unicodeRanges, 96, 32)
        else:
            os2.recalcUnicodeRanges(self.otf)

        codepageRanges = data.OS2_codepageRanges(ctx)
        if codepageRanges is None:
            codepageRanges = FontProc.codepage_ranges(
                ctx, self.unicodeToGlyphNameMap.keys())
        os2.ulCodePageRange1 = conversion.to_bitflags(codepageRanges, 0, 32)
        os2.ulCodePageRange2 = conversion.to_bitflags(codepageRanges, 32, 32)

        os2.achVendID = data.OS2_vendorID(ctx)

        os2.sxHeight = otRound(data.xHeight(ctx))
        os2.sCapHeight = otRound(data.capHeight(ctx))
        os2.sTypoAscender, \
        os2.sTypoDescender, \
        os2.sTypoLineGap = otRoundSequence(data.OS2_typoMetrics(ctx))
        os2.usWinAscent, \
        os2.usWinDescent = otRoundSequence(data.OS2_winMetrics(ctx, self.fontBounds))

        os2.fsSelection = data.OS2_fsSelection(ctx)

        os2.fsFirstCharIndex, \
        os2.fsLastCharIndex = FontProc.minmax_cids(ctx, self.unicodeToGlyphNameMap.keys())
        os2.usBreakChar = 32
        os2.usDefaultChar = 0
        # maximum contextual lookup length
        os2.usMaxContext = 0

    def build_post(self):
        ctx = self.ctx
        data = self.metadataProvider
        self.otf["post"] = post = ttLib.newTable("post")
        post.formatType = 3.0

        post.italicAngle = data.italicAngle(ctx)

        post.underlinePosition = otRound(data.post_underlinePosition(ctx))
        post.underlineThickness = otRound(data.post_underlineThickness(ctx))
        post.isFixedPitch = data.post_isFixedPitch(ctx)

        post.minMemType42 = 0
        post.maxMemType42 = 0
        post.minMemType1 = 0
        post.maxMemType1 = 0

    def build_others(self):
        pass


class Type2FontCompiler(BaseFontCompiler):
    sfntVersion = "OTTO"

    def __init__(self, font, mastername=None,
                 roundTolerance=None, optimizeCFF=True):
        if roundTolerance is not None:
            self.roundTolerance = float(roundTolerance)
        else:
            # round all coordinates to integers by default
            self.roundTolerance = 0.5
        super().__init__(font, mastername)
        self.optimizeCFF = optimizeCFF

    def build_CFF(self):
        ctx = self.ctx
        data = self.metadataProvider
        self.otf["CFF "] = cff = ttLib.newTable("CFF ")
        cff = cff.cff

        cff.major = 1
        cff.minor = 0
        cff.hdrSize = 4
        cff.offSize = 4

        cff.fontNames = []
        strings = IndexedStrings()
        cff.strings = strings
        private = PrivateDict(strings=strings)
        private.rawDict.update(private.defaults)
        globalSubrs = GlobalSubrsIndex(private=private)
        topDict = TopDict(GlobalSubrs=globalSubrs, strings=strings)
        topDict.Private = private
        charStrings = topDict.CharStrings = CharStrings(
            file=None,
            charset=None,
            globalSubrs=globalSubrs,
            private=private,
            fdSelect=None,
            fdArray=None,
        )
        charStrings.charStringsAreIndexed = True
        topDict.charset = []
        charStringsIndex = charStrings.charStringsIndex = SubrsIndex(
            private=private, globalSubrs=globalSubrs
        )
        cff.topDictIndex = topDictIndex = TopDictIndex()
        topDictIndex.append(topDict)
        topDictIndex.strings = strings
        cff.GlobalSubrs = globalSubrs

        cff.fontNames.append(
            data.name_postscriptFontName(ctx))
        topDict = cff.topDictIndex[0]
        topDict.version = data.version(ctx)
        topDict.Notice = conversion.to_postscript_string(
            data.name_trademark(ctx),
            lambda result: ctx.log.append(
                semlog.warning_attr_truncated(attr="trademark", result=result)
            )
        )
        topDict.Copyright = conversion.to_postscript_string(
            data.copyright(ctx),
            lambda result: ctx.log.append(
                semlog.warning_attr_truncated(attr="copyright", result=result)
            )
        )
        topDict.FullName = data.name_postscriptFullName(ctx)
        topDict.FamilyName = data.CFF_postscriptFamilyName(ctx)
        topDict.Weight = data.CFF_postscriptWeightName(ctx)

        topDict.isFixedPitch = data.post_isFixedPitch(ctx)
        topDict.ItalicAngle = data.italicAngle(ctx)
        topDict.UnderlinePosition = otRound(
            data.post_underlinePosition(ctx))
        topDict.UnderlineThickness = otRound(
            data.post_underlineThickness(ctx))

        scale = 1.0 / otRound(data.unitsPerEm(ctx))
        topDict.FontMatrix = [
            scale, 0, 0, scale, 0, 0]

        defaultWidthX, nominalWidthX = FontProc.postscript_width_stats(ctx, self.otf)
        if defaultWidthX:
            private.rawDict["defaultWidthX"] = defaultWidthX
        if nominalWidthX:
            private.rawDict["nominalWidthX"] = nominalWidthX

        blueFuzz = otRound(
            data.CFF_postscriptBlueFuzz(ctx))
        blueShift = otRound(
            data.CFF_postscriptBlueShift(ctx))
        blueScale = data.CFF_postscriptBlueScale(ctx)
        forceBold = data.CFF_postscriptForceBold(ctx)
        blueValues = otRoundSequence(data.CFF_postscriptBlueValues(ctx))
        otherBlues = otRoundSequence(data.CFF_postscriptOtherBlues(ctx))
        familyBlues = otRoundSequence(data.CFF_postscriptFamilyBlues(ctx))
        familyOtherBlues = otRoundSequence(data.CFF_postscriptFamilyOtherBlues(ctx))
        stemSnapH = otRoundSequence(data.CFF_postscriptStemSnapH(ctx))
        stemSnapV = otRoundSequence(data.CFF_postscriptStemSnapV(ctx))
        # only write the blues data if some blues are defined.
        if any((blueValues, otherBlues, familyBlues, familyOtherBlues)):
            private.rawDict["BlueFuzz"] = blueFuzz
            private.rawDict["BlueShift"] = blueShift
            private.rawDict["BlueScale"] = blueScale
            private.rawDict["ForceBold"] = forceBold
            if blueValues:
                private.rawDict["BlueValues"] = blueValues
            if otherBlues:
                private.rawDict["OtherBlues"] = otherBlues
            if familyBlues:
                private.rawDict["FamilyBlues"] = familyBlues
            if familyOtherBlues:
                private.rawDict["FamilyOtherBlues"] = familyOtherBlues
        # only write the stems if both are defined.
        if stemSnapH and stemSnapV:
            private.rawDict["StemSnapH"] = stemSnapH
            private.rawDict["StdHW"] = stemSnapH[0]
            private.rawDict["StemSnapV"] = stemSnapV
            private.rawDict["StdVW"] = stemSnapV[0]
        # populate glyphs
        for glyphName in self.glyphOrder:
            glyph = self.glyphMap[glyphName]
            charString = self.draw_charstring(glyph, private, globalSubrs)

            # add to the font
            charStringsIndex.append(charString)
            glyphID = len(topDict.charset)
            charStrings.charStrings[glyphName] = glyphID
            topDict.charset.append(glyphName)
        bounds = self.fontBounds
        topDict.FontBBox = (bounds.left, bounds.bottom, bounds.right, bounds.top)

    def build_maxp(self):
        self.otf["maxp"] = maxp = ttLib.newTable("maxp")
        maxp.tableVersion = 0x00005000
        maxp.numGlyphs = len(self.glyphOrder)

    def build_others(self):
        self.build_CFF()

    #

    def draw_charstring(self, glyph, private, globalSubrs):
        ctx = self.ctx
        data = self.metadataProvider
        layer = data.glyph_layer(ctx, glyph)

        width = data.layer_width(ctx, layer)
        defaultWidth = private.defaultWidthX
        nominalWidth = private.nominalWidthX
        if width == defaultWidth:
            # if width equals the default it can be omitted from charstring
            width = None
        else:
            # subtract the nominal width
            width -= nominalWidth
        if width is not None:
            width = otRound(width)

        pen = T2CharStringPen(width, self.glyphOrder, roundTolerance=self.roundTolerance)
        drawing.draw_layer(layer, pen)
        charString = pen.getCharString(private, globalSubrs, optimize=self.optimizeCFF)
        return charString
