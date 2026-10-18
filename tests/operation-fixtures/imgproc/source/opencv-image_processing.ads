package OpenCV.Image_Processing is
--  Native squared box filtering (cv::sqrBoxFilter): for every pixel and
   --  channel, sums the squares of the Source samples in a Kernel_Size
   --  window and, for Mean_Square, divides by the effective kernel area.
   --  Returns fresh independent Float64 storage with Source's rows, columns
   --  and channel count; Source is unchanged.
   --
   --  Source must be nonempty 2-D UInt8 or Float32 with 1 or 3 channels.
   --  The window for column X starts at `X - Width / 2` and spans Width
   --  columns, and rows likewise, so positive odd, even and oversized
   --  kernels are all accepted. Normalized nonconstant singleton axes
   --  reduce to one: with Mean_Square and a Border other than
   --  Constant_Border, a one-column or one-row Source uses a kernel
   --  dimension of one on that axis; Constant_Border and Sum_Of_Squares
   --  keep the requested dimensions. The UInt8 effective area is at most
   --  33025 (native signed accumulator) and the Float32 area at most
   --  2_147_483_647; other unsafe native signed arithmetic is rejected.
   --
   --  Regions are isolated: only the Region's logical pixels are read and
   --  border extrapolation never reaches the parent. Float32 retains native
   --  incremental rounding and NaN/Inf propagation, which can persist
   --  beyond the ideal mathematical local window; tiny finite residuals
   --  after large values may be lost. This is not an exact per-window sum.
   --  @param Source Image whose squared samples are summed.
   --  @param Kernel_Size Window width and height in pixels; both must be
   --  positive and may be even or exceed the image.
   --  @param Mode Mean_Square (default) divides by the effective area;
   --  Sum_Of_Squares returns the plain sum.
   --  @param Border Extrapolation outside Source: Constant_Border (zero
   --  samples, still counted in the Mean_Square area), Replicate, Reflect
   --  or Reflect_101 (default). Wrap is rejected.
   --  @return Fresh owning Float64 Mat with one squared-window value per
   --  Source pixel and channel.
   --  @exception OpenCV_Error Raised for an empty, non-2-D or
   --  unsupported Source, a zero kernel dimension, Wrap, an effective area
   --  above its limit, unsafe native arithmetic, or a native failure.
   function Squared_Box_Filter
     (Source      : OpenCV.Core.Mat;
      Kernel_Size : OpenCV.Size;
      Mode        : Squared_Box_Mode := Mean_Square;
      Border      : OpenCV.Border_Kind := OpenCV.Reflect_101)
      return OpenCV.Core.Mat;
--  Get_Gaussian_Kernel returns an N x 1 single-channel Gaussian coefficient
   --  vector of the requested Depth (native cv::getGaussianKernel), where N
   --  is Kernel_Size, as fresh owning storage. This overload asks OpenCV to
   --  derive sigma from Kernel_Size; there is no public zero or negative
   --  sigma sentinel. Coefficients preserve OpenCV's values and ordering:
   --  they are symmetric and sum to 1 within rounding, and Kernel_Size 1
   --  yields exactly 1.0. The vector may be passed directly to
   --  Sep_Filter_2D as Kernel_X and Kernel_Y.
   --  @param Kernel_Size Number of coefficients N; must be odd.
   --  @param Depth Coefficient depth; Float64_Kernel by default.
   --  @return Fresh N x 1 coefficient vector.
   --  @exception OpenCV_Error Raised for an even Kernel_Size or a
   --  failure reported by OpenCV.
   function Get_Gaussian_Kernel
     (Kernel_Size : Gaussian_Kernel_Size;
      Depth       : Gaussian_Kernel_Depth := Float64_Kernel)
      return OpenCV.Core.Mat;
--  This overload is the same Get_Gaussian_Kernel generator with an
   --  explicit Sigma: it returns a fresh owning N x 1 single-channel vector
   --  of symmetric Gaussian coefficients of the requested Depth, in
   --  OpenCV's order. Zero and negative values are rejected rather than
   --  switching to automatic sigma. Used as both Sep_Filter_2D kernels, it
   --  gives the Gaussian_Blur result for the same size and Sigma, up to
   --  rounding.
   --  @param Kernel_Size Number of coefficients N; must be odd.
   --  @param Sigma Gaussian standard deviation in coefficient (pixel)
   --  units; must be finite and strictly greater than zero.
   --  @param Depth Coefficient depth; Float64_Kernel by default.
   --  @return Fresh N x 1 coefficient vector.
   --  @exception OpenCV_Error Raised for an even Kernel_Size, a zero,
   --  negative or nonfinite Sigma, or a failure reported by OpenCV.
   function Get_Gaussian_Kernel
     (Kernel_Size : Gaussian_Kernel_Size;
      Sigma       : OpenCV.Float64_Value;
      Depth       : Gaussian_Kernel_Depth := Float64_Kernel)
      return OpenCV.Core.Mat;
--  Pyramid_Up performs OpenCV's Gaussian-pyramid upsampling of Source
   --  (native cv::pyrUp). Source must be a non-empty two-dimensional Mat
   --  with depth UInt8, UInt16, Int16, Float32, or Float64. Channel count is
   --  unrestricted. Destination receives Source's depth and channel count
   --  with exactly doubled rows and columns. A Region is processed as its
   --  own logical image, without parent pixels. OpenCV supports only its
   --  default border (Reflect_101) for this operation, so no Border
   --  parameter is exposed. Pyramid_Up after Pyramid_Down is generally a
   --  smoothed reconstruction, not the original image.
   --
   --  Destination is a direct native output: storage that already has the
   --  result's size and type is reused (shallow copies and a Region's parent
   --  see the result); otherwise Destination is rebound to new storage.
   --  Direct in-place operation is not supported: a Destination that is
   --  Source or shares or overlaps its storage, including overlapping
   --  Regions, is rejected. Extreme geometries are rejected before native
   --  signed-int pyramid arithmetic can overflow.
   --  @param Source Image to upsample.
   --  @param Destination Receives the double-size image.
   --  @exception OpenCV_Error Raised for an empty, non-2-D, or
   --  unsupported-depth Source, aliased or overlapping Source and
   --  Destination storage, an unsafe geometry, or a failure reported by
   --  OpenCV.
   procedure Pyramid_Up
     (Source : OpenCV.Core.Mat; Destination : in out OpenCV.Core.Mat);
--  Pyramid_Up with an explicit Output_Size performs the same Gaussian
   --  upsampling (native cv::pyrUp, default border) to the requested size.
   --  Each extent must equal twice the Source extent or one less than that
   --  (for example 5 -> 9 or 5 -> 10), so every natural Pyramid_Down
   --  geometry, including odd sizes, can be reversed exactly. Other sizes,
   --  including OpenCV's nonportable twice-plus-one extent, are rejected
   --  before any native allocation. The Source contract matches the natural
   --  overload. The result is computed into fresh storage and bound to
   --  Destination only on success; on failure Destination is unchanged.
   --  Destination may therefore share Source storage.
   --  @param Source Image to upsample.
   --  @param Destination Rebound on success to the upsampled image, with
   --  Source's depth and channel count.
   --  @param Output_Size Requested Width (columns) and Height (rows); each
   --  is `2 * N` or `2 * N - 1` for the corresponding Source extent N.
   --  @exception OpenCV_Error Raised for an invalid Source, an
   --  Output_Size extent other than `2 * N` or `2 * N - 1`, an unsafe
   --  geometry, or a failure reported by OpenCV.
   procedure Pyramid_Up
     (Source      : OpenCV.Core.Mat;
      Destination : in out OpenCV.Core.Mat;
      Output_Size : OpenCV.Size);
--  Bilateral_Filter replaces Destination with an edge-preserving smoothing
   --  of Source (native cv::bilateralFilter). Spatial distance and
   --  pixel/color distance both weight the neighborhood average, so strong
   --  intensity or color discontinuities are preserved more than with a
   --  linear blur. Source must be a non-empty two-dimensional Mat of depth
   --  UInt8 or Float32 with exactly 1 or 3 channels. For 3-channel Sources,
   --  color-distance weighting uses the combined color difference rather
   --  than filtering channels independently. This overload asks OpenCV to
   --  derive the neighborhood diameter from Sigma_Space; there is no public
   --  zero or negative diameter sentinel.
   --
   --  Destination receives Source's rows, columns, depth, and channel count
   --  as a direct native output: storage that already has that size and
   --  type is reused (shallow copies and a Region's parent see the result);
   --  otherwise Destination is rebound to new storage. Direct in-place
   --  operation is not supported: Destination being Source, or a header
   --  whose data starts at Source's first element, is rejected. Source
   --  remains unchanged when Destination is distinct.
   --  @param Source Image to smooth.
   --  @param Destination Receives the filtered image; must not alias Source.
   --  @param Sigma_Color Standard deviation of the intensity/color-distance
   --  weight; a small value preserves discontinuities more. Positive and
   --  finite.
   --  @param Sigma_Space Standard deviation of the spatial-distance weight,
   --  in pixels; it also determines the neighborhood diameter. Positive and
   --  finite.
   --  @param Border Extrapolation outside Source: Constant_Border,
   --  Replicate, Reflect, or Reflect_101 (default). Wrap is rejected.
   --  @exception OpenCV_Error Raised for an empty, non-2-D, or
   --  unsupported Source, a nonpositive or nonfinite sigma, Wrap, a
   --  Destination aliasing Source, or a failure reported by OpenCV.
   procedure Bilateral_Filter
     (Source      : OpenCV.Core.Mat;
      Destination : in out OpenCV.Core.Mat;
      Sigma_Color : OpenCV.Float64_Value;
      Sigma_Space : OpenCV.Float64_Value;
      Border      : OpenCV.Border_Kind := OpenCV.Reflect_101);
--  This overload is the same Bilateral_Filter operation with an explicit
   --  neighborhood Diameter. Diameter is a positive integer and need not be
   --  odd. OpenCV uses Diameter as the neighborhood size independently of
   --  Sigma_Space; Sigma_Space still weights samples inside that
   --  neighborhood. Source requirements, borders, and the direct native
   --  Destination output match the automatic overload. Direct in-place
   --  operation is not supported.
   --  @param Source UInt8 or Float32 image with 1 or 3 channels to smooth.
   --  @param Destination Receives the filtered image with Source's
   --  geometry and type; must not alias Source.
   --  @param Diameter Neighborhood diameter in pixels; any positive value.
   --  @param Sigma_Color Standard deviation of the intensity/color-distance
   --  weight; positive and finite.
   --  @param Sigma_Space Standard deviation of the spatial-distance weight
   --  in pixels, applied inside the Diameter neighborhood; positive and
   --  finite.
   --  @param Border Extrapolation outside Source: Constant_Border,
   --  Replicate, Reflect, or Reflect_101 (default). Wrap is rejected.
   --  @exception OpenCV_Error Raised for an invalid Source, a
   --  nonpositive or nonfinite sigma, Wrap, a Destination aliasing Source,
   --  or a failure reported by OpenCV.
   procedure Bilateral_Filter
     (Source      : OpenCV.Core.Mat;
      Destination : in out OpenCV.Core.Mat;
      Diameter    : Bilateral_Diameter;
      Sigma_Color : OpenCV.Float64_Value;
      Sigma_Space : OpenCV.Float64_Value;
      Border      : OpenCV.Border_Kind := OpenCV.Reflect_101);
--  Filter_2D replaces Destination with a linear correlation of Source
   --  against Kernel (native cv::filter2D). This is correlation, not
   --  mathematical convolution: the kernel is not mirrored around the
   --  anchor. For every channel,
   --
   --       Destination (x, y) = Offset + sum over kernel positions (i, j)
   --         of Kernel (i, j) * Source (x + i - Anchor.X, y + j - Anchor.Y)
   --
   --  where i is a kernel column, j a kernel row, and Anchor the kernel
   --  position aligned with the output pixel. This overload uses OpenCV's
   --  centered default anchor; there is no public (-1, -1) sentinel. Source
   --  must be a non-empty two-dimensional Mat of depth UInt8, UInt16, Int16,
   --  Float32, or Float64. Channel count is unrestricted; the same
   --  single-channel Kernel is applied independently to every Source
   --  channel. Kernel dimensions need not be odd, square, or normalized.
   --
   --  Destination receives Source's rows, columns, and channel count, with
   --  the requested depth, as a direct native output: storage that already
   --  has that size and type is reused (shallow copies and a Region's
   --  parent see the result); otherwise Destination is rebound to new
   --  storage. Direct in-place operation is supported when the requested
   --  destination depth matches Source; a depth-changing alias (Destination
   --  is Source or starts at its first element) is rejected. Source remains
   --  unchanged when Destination is distinct.
   --  @param Source Image to filter.
   --  @param Destination Receives the filtered image.
   --  @param Kernel Correlation coefficients: a non-empty two-dimensional
   --  single-channel Float32 or Float64 Mat of any size. It must not share
   --  Destination's storage.
   --  @param Destination_Depth Output depth, Same_Depth by default; the
   --  supported source/destination combinations are those of Sobel and
   --  Laplacian (see Derivative_Depth).
   --  @param Offset Value added to each filtered value; must be finite.
   --  @param Border Extrapolation outside Source: Constant_Border,
   --  Replicate, Reflect, or Reflect_101 (default). Wrap is rejected.
   --  @exception OpenCV_Error Raised for an empty, non-2-D, or
   --  unsupported Source or Kernel, an unsupported depth combination, a
   --  nonfinite Offset, Wrap, a rejected alias, or a failure reported by
   --  OpenCV.
   procedure Filter_2D
     (Source            : OpenCV.Core.Mat;
      Destination       : in out OpenCV.Core.Mat;
      Kernel            : OpenCV.Core.Mat;
      Destination_Depth : Filter_Depth := Same_Depth;
      Offset            : OpenCV.Float64_Value := 0.0;
      Border            : OpenCV.Border_Kind := OpenCV.Reflect_101);
--  This overload is the same Filter_2D correlation with an explicit Kernel
   --  Anchor. Anchor must lie inside Kernel: X and Y are nonnegative and
   --  strictly less than Kernel's columns and rows. There is no public mixed
   --  or centered (-1, -1) sentinel in this overload. Source, Kernel, depth,
   --  Offset, border, and direct native Destination rules match the
   --  centered overload. Direct in-place operation is supported when the
   --  requested destination depth matches Source.
   --  @param Source Image to filter.
   --  @param Destination Receives the filtered image.
   --  @param Kernel Non-empty two-dimensional single-channel Float32 or
   --  Float64 correlation coefficients; must not share Destination's
   --  storage.
   --  @param Anchor Kernel position aligned with each output pixel:
   --  column X and row Y within Kernel.
   --  @param Destination_Depth Output depth, Same_Depth by default; see
   --  Derivative_Depth for the supported combinations.
   --  @param Offset Value added to each filtered value; must be finite.
   --  @param Border Extrapolation outside Source: Constant_Border,
   --  Replicate, Reflect, or Reflect_101 (default). Wrap is rejected.
   --  @exception OpenCV_Error Raised for an Anchor outside Kernel,
   --  any input rejected by the centered overload, or a failure reported by
   --  OpenCV.
   procedure Filter_2D
     (Source            : OpenCV.Core.Mat;
      Destination       : in out OpenCV.Core.Mat;
      Kernel            : OpenCV.Core.Mat;
      Anchor            : OpenCV.Point;
      Destination_Depth : Filter_Depth := Same_Depth;
      Offset            : OpenCV.Float64_Value := 0.0;
      Border            : OpenCV.Border_Kind := OpenCV.Reflect_101);
end OpenCV.Image_Processing;
