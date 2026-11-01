with Interfaces;

--  Root package of the Ada binding to OpenCV.
--
--  This package owns the value types shared by every module crate: numeric
--  element subtypes, integer and binary32 geometry, Scalar, and the common
--  Border_Kind and Angle_Unit options. Module packages such as OpenCV.Core
--  and crates that depend on opencv_core reuse these declarations instead of
--  redeclaring them. OpenCV.Core owns Mat and matrix-specific abstractions.
--
--  The types here describe how values are represented. Whether a particular
--  value is acceptable is decided by each operation that consumes it.

package OpenCV is

   --  Raised when OpenCV or the native binding layer reports a failure that
   --  the Ada API does not map to a more specific exception.
   OpenCV_Error : exception;

   --  Shared public value types owned by the root OpenCV package and
   --  distributed by the opencv_core crate. OpenCV.Core owns Mat and
   --  matrix-specific abstractions; other module crates reuse these
   --  values without redeclaring them.

   --  CV_8U, CV_8S, CV_16U, CV_16S, CV_32S, CV_32F, and CV_64F element
   --  value domains used by typed Mat accessors and shared numeric
   --  APIs. Float16 remains Core-specific.
   --
   --  Unsigned 8-bit element value (CV_8U).
   subtype UInt8_Value is Interfaces.Unsigned_8;

   --  Signed 8-bit element value (CV_8S).
   subtype Int8_Value is Interfaces.Integer_8;

   --  Unsigned 16-bit element value (CV_16U).
   subtype UInt16_Value is Interfaces.Unsigned_16;

   --  Signed 16-bit element value (CV_16S).
   subtype Int16_Value is Interfaces.Integer_16;

   --  Signed 32-bit element value (CV_32S).
   subtype Int32_Value is Interfaces.Integer_32;

   --  IEEE binary32 element value (CV_32F).
   subtype Float32_Value is Interfaces.IEEE_Float_32;

   --  IEEE binary64 element value (CV_64F).
   subtype Float64_Value is Interfaces.IEEE_Float_64;

   --  Nonnegative 32-bit integer extent, used for widths and heights.
   --  The type represents zero through Integer_32'Last. Individual
   --  operations may accept only a subset, for example requiring a positive
   --  extent or one that fits a particular image.
   type Size_Coordinate is
     new Interfaces.Integer_32 range 0 .. Interfaces.Integer_32'Last;

   --  Signed 32-bit integer coordinate, used for point positions and
   --  rectangle origins. Negative values are representable. Individual
   --  operations define which positions they accept, for example Mat
   --  element access requires coordinates inside the matrix.
   type Point_Coordinate is new Interfaces.Integer_32;

   --  Integer two-dimensional extent.
   --  Both components are nonnegative Size_Coordinate values.
   --  @field Width Horizontal extent, in the same units as Point.X.
   --  @field Height Vertical extent, in the same units as Point.Y.
   type Size is record
      Width  : Size_Coordinate := 0;
      Height : Size_Coordinate := 0;
   end record;

   --  Integer two-dimensional point with signed 32-bit coordinates.
   --  Mat indices are zero-based, so (0, 0) addresses the first row and
   --  column. The type itself places no bounds on either coordinate.
   --  @field X Horizontal coordinate (column direction).
   --  @field Y Vertical coordinate (row direction).
   type Point is record
      X : Point_Coordinate := 0;
      Y : Point_Coordinate := 0;
   end record;

   --  A zero-based, value-semantic sequence of points. An empty result has
   --  the null range 1 .. 0.
   type Point_Array is array (Natural range <>) of Point;

   --  Shared value-semantic 3-D point with signed 32-bit coordinates.
   --  @field X Horizontal coordinate.
   --  @field Y Vertical coordinate.
   --  @field Z Third spatial coordinate, independent of the image plane.
   type Point_3D is record
      X : Point_Coordinate := 0;
      Y : Point_Coordinate := 0;
      Z : Point_Coordinate := 0;
   end record;

   --  Preserves arbitrary Natural bounds; null arrays are valid values.
   type Point_3D_Array is array (Natural range <>) of Point_3D;

   --  Axis-aligned rectangle with a signed origin and nonnegative size.
   --  OpenCV rectangle origins may be negative. Width and Height remain
   --  nonnegative in this Ada value model. A Rect is not restricted merely
   --  because Mat ROI operations require nonnegative origins; Mat.Region
   --  enforces that ROI-specific constraint itself.
   --  @field X Horizontal coordinate of the signed origin.
   --  @field Y Vertical coordinate of the signed origin.
   --  @field Width Nonnegative horizontal extent from the origin.
   --  @field Height Nonnegative vertical extent from the origin.
   type Rect is record
      X      : Point_Coordinate := 0;
      Y      : Point_Coordinate := 0;
      Width  : Size_Coordinate := 0;
      Height : Size_Coordinate := 0;
   end record;

   --  Value-semantic 2-D point with binary32 coordinates. This is the
   --  shared representation for OpenCV floating-point 2-D points.
   --  @field X Horizontal coordinate, as a binary32 value.
   --  @field Y Vertical coordinate, as a binary32 value.
   type Float32_Point is record
      X : Float32_Value := 0.0;
      Y : Float32_Value := 0.0;
   end record;

   --  Shared value-semantic 3-D point with binary32 coordinates. NaN and
   --  infinities are representable; finiteness is operation-specific policy,
   --  not an invariant of this value type.
   --  @field X Horizontal coordinate, as a binary32 value.
   --  @field Y Vertical coordinate, as a binary32 value.
   --  @field Z Third spatial coordinate, as a binary32 value.
   type Float32_Point_3D is record
      X : Float32_Value := 0.0;
      Y : Float32_Value := 0.0;
      Z : Float32_Value := 0.0;
   end record;

   --  Preserves arbitrary Natural bounds; null arrays are valid values.
   type Float32_Point_3D_Array is array (Natural range <>) of Float32_Point_3D;

   --  Value-semantic two-dimensional binary32 extent. Individual operations
   --  define whether negative dimensions are meaningful.
   --  @field Width Horizontal extent, as a binary32 value.
   --  @field Height Vertical extent, as a binary32 value.
   type Float32_Size is record
      Width  : Float32_Value := 0.0;
      Height : Float32_Value := 0.0;
   end record;

   --  Value-semantic rotated rectangle with binary32 native OpenCV fields.
   --  Angle_Degrees is deliberately not normalized because different OpenCV
   --  operations and versions can use distinct equivalent representations.
   --  @field Center Center point of the rectangle.
   --  @field Size Width and height of the rectangle.
   --  @field Angle_Degrees Rotation angle in degrees, stored as given by the
   --  producer or caller. No normalization range or rotation direction is
   --  guaranteed by this type.
   type Rotated_Rect is record
      Center        : Float32_Point := (X => 0.0, Y => 0.0);
      Size          : Float32_Size := (Width => 0.0, Height => 0.0);
      Angle_Degrees : Float32_Value := 0.0;
   end record;

   --  Ordered quadruple of binary64 values, the counterpart of cv::Scalar.
   --  It is used for per-channel values such as fill colors. The type only
   --  stores four numbers; it does not select or enforce a color space.
   --  @field Component_0 First component (channel 0).
   --  @field Component_1 Second component (channel 1).
   --  @field Component_2 Third component (channel 2).
   --  @field Component_3 Fourth component (channel 3).
   type Scalar is record
      Component_0 : Long_Float := 0.0;
      Component_1 : Long_Float := 0.0;
      Component_2 : Long_Float := 0.0;
      Component_3 : Long_Float := 0.0;
   end record;

   --  Build a Scalar from up to four components in channel order.
   --  Component_0 is stored first; how the components map to colors is
   --  determined by the operation that consumes the Scalar.
   --  @param Component_0 Value stored in component 0.
   --  @param Component_1 Value stored in component 1. Defaults to 0.0.
   --  @param Component_2 Value stored in component 2. Defaults to 0.0.
   --  @param Component_3 Value stored in component 3. Defaults to 0.0.
   --  @return A Scalar whose components equal the arguments.
   function Make_Scalar
     (Component_0 : Long_Float;
      Component_1 : Long_Float := 0.0;
      Component_2 : Long_Float := 0.0;
      Component_3 : Long_Float := 0.0) return Scalar
   is (Component_0 => Component_0,
       Component_1 => Component_1,
       Component_2 => Component_2,
       Component_3 => Component_3);

   --  Rule for supplying pixels outside the image boundary, corresponding
   --  to OpenCV's cv::BorderTypes. Individual operations may support only
   --  some of these kinds and define any further restrictions.
   --  @enum Constant_Border Outside pixels take a caller-supplied constant
   --  value.
   --  @enum Replicate The outermost pixel is repeated outward.
   --  @enum Reflect The image is mirrored about the edge, repeating the edge
   --  pixel.
   --  @enum Reflect_101 The image is mirrored about the edge without
   --  repeating the edge pixel.
   --  @enum Wrap The image is treated as periodic and continues from the
   --  opposite edge.
   type Border_Kind is
     (Constant_Border, Replicate, Reflect, Reflect_101, Wrap);

   --  Unit used to express an angle.
   --  @enum Radians Angles are measured in radians.
   --  @enum Degrees Angles are measured in degrees.
   type Angle_Unit is (Radians, Degrees);

end OpenCV;
