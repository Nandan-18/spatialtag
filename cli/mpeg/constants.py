"""MPEG-4 constants."""

TRAK_TYPE_VIDE = b"vide"

# Leaf types.
TAG_STCO = b"stco"
TAG_CO64 = b"co64"
TAG_FREE = b"free"
TAG_MDAT = b"mdat"
TAG_XML = b"xml "
TAG_HDLR = b"hdlr"
TAG_FTYP = b"ftyp"
TAG_ESDS = b"esds"
TAG_SOUN = b"soun"
TAG_VIDE = b"vide"
TAG_TKHD = b"tkhd"
TAG_SA3D = b"SA3D"

TAG_PRHD = b"prhd"
TAG_EQUI = b"equi"
TAG_SVHD = b"svhd"
TAG_ST3D = b"st3d"

# Container types.
TAG_MOOV = b"moov"
TAG_UDTA = b"udta"
TAG_META = b"meta"
TAG_TRAK = b"trak"
TAG_MDIA = b"mdia"
TAG_MINF = b"minf"
TAG_STBL = b"stbl"
TAG_STSD = b"stsd"
TAG_UUID = b"uuid"
TAG_WAVE = b"wave"

TAG_SV3D = b"sv3d"
TAG_PROJ = b"proj"


# Sound sample descriptions.
TAG_NONE = b"NONE"
TAG_RAW_ = b"raw "
TAG_TWOS = b"twos"
TAG_SOWT = b"sowt"
TAG_FL32 = b"fl32"
TAG_FL64 = b"fl64"
TAG_IN24 = b"in24"
TAG_IN32 = b"in32"
TAG_ULAW = b"ulaw"
TAG_ALAW = b"alaw"
TAG_LPCM = b"lpcm"
TAG_MP4A = b"mp4a"
TAG_OPUS = b"Opus"

# Video sample descriptions.
TAG_AVC1 = b"avc1"
TAG_VP09 = b"vp09"
TAG_AV01 = b"av01"
TAG_HEV1 = b"hev1"
TAG_HVC1 = b"hvc1"
TAG_DVH1 = b"dvh1"
TAG_APCN = b"apcn"
TAG_APCH = b"apch"
TAG_APCS = b"apcs"
TAG_APCO = b"apco"
TAG_AP4H = b"ap4h"
TAG_AP4X = b"ap4x"

SOUND_SAMPLE_DESCRIPTIONS = frozenset(
    [
        TAG_NONE,
        TAG_RAW_,
        TAG_TWOS,
        TAG_SOWT,
        TAG_FL32,
        TAG_FL64,
        TAG_IN24,
        TAG_IN32,
        TAG_ULAW,
        TAG_ALAW,
        TAG_LPCM,
        TAG_MP4A,
        TAG_OPUS,
    ]
)

VIDEO_SAMPLE_DESCRIPTIONS = frozenset(
    [
        TAG_NONE,
        TAG_AVC1,
        TAG_VP09,
        TAG_AV01,
        TAG_HEV1,
        TAG_HVC1,
        TAG_DVH1,
        TAG_APCN,
        TAG_APCH,
        TAG_APCS,
        TAG_APCO,
        TAG_AP4H,
        TAG_AP4X,
    ]
)

CONTAINERS_LIST = (
    frozenset(
        [
            TAG_MDIA,
            TAG_MINF,
            TAG_MOOV,
            TAG_STBL,
            TAG_STSD,
            TAG_TRAK,
            TAG_UDTA,
            TAG_WAVE,
            TAG_SV3D,
            TAG_PROJ,
        ]
    )
    .union(SOUND_SAMPLE_DESCRIPTIONS)
    .union(VIDEO_SAMPLE_DESCRIPTIONS)
)
