namespace NAPS2.Images.Bitwise;

internal class PaperFrameImageOp(PaperFrameTransform frame) : BinaryBitwiseImageOp
{
    protected override LockMode SrcLockMode => LockMode.ReadOnly;
    protected override LockMode DstLockMode => LockMode.WriteOnly;
    protected override int GetPartitionSize(BitwiseImageData src, BitwiseImageData dst) => dst.h;
    protected override int GetPartitionCount(BitwiseImageData src, BitwiseImageData dst) => 1;
    protected override void ValidateCore(BitwiseImageData src, BitwiseImageData dst)
    {
        var g = frame.Geometry(src.w, src.h);
        if (src.bytesPerPixel is not (3 or 4) || dst.bytesPerPixel is not (3 or 4) ||
            src.invertColorSpace || dst.invertColorSpace || dst.w != g.width || dst.h != g.height)
            throw new ArgumentException("Unsupported paper frame image");
    }
    protected override unsafe void PerformCore(BitwiseImageData src, BitwiseImageData dst, int start, int end)
    {
        var g = frame.Geometry(src.w, src.h);
        for (int y = start; y < end; y++)
        {
            var row = dst.ptr + (dst.invertY ? dst.h - 1 - y : y) * dst.stride;
            double v = g.v + y;
            for (int x = 0; x < dst.w; x++)
            {
                var p = row + x * dst.bytesPerPixel;
                double u = g.u + x;
                double sx = g.c * u + g.s * v, sy = -g.s * u + g.c * v;
                if (sx < 0 || sy < 0 || sx > src.w - 1 || sy > src.h - 1)
                {
                    for (int k = 0; k < dst.bytesPerPixel; k++) p[k] = 255;
                    continue;
                }
                int x0 = (int)sx, y0 = (int)sy;
                int x1 = Math.Min(x0 + 1, src.w - 1), y1 = Math.Min(y0 + 1, src.h - 1);
                var r0 = src.ptr + (src.invertY ? src.h - 1 - y0 : y0) * src.stride;
                var r1 = src.ptr + (src.invertY ? src.h - 1 - y1 : y1) * src.stride;
                double fx = sx - x0, fy = sy - y0;
                byte Read(int offset)
                {
                    double a = r0[x0 * src.bytesPerPixel + offset] * (1 - fx) + r0[x1 * src.bytesPerPixel + offset] * fx;
                    double b = r1[x0 * src.bytesPerPixel + offset] * (1 - fx) + r1[x1 * src.bytesPerPixel + offset] * fx;
                    return (byte)Math.Round(a * (1 - fy) + b * fy);
                }
                p[dst.rOff] = Read(src.rOff); p[dst.gOff] = Read(src.gOff); p[dst.bOff] = Read(src.bOff);
                if (dst.hasAlpha) p[dst.aOff] = src.hasAlpha ? Read(src.aOff) : (byte)255;
            }
        }
    }
}

// Modified by Pengusto on 2026-10-25: ES-60W free-helper release preparation.
