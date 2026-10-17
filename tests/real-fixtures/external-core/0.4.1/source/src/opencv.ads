with Interfaces;

package OpenCV is

   OpenCV_Error : exception;

   --  Shared public value types owned by the root OpenCV package and
   --  distributed by the opencv_core crate. OpenCV.Core owns Mat and
   --  matrix-specific abstractions; other module crates reuse these
   --  values without redeclaring them.

   --  CV_8U, CV_8S, CV_16U, CV_16S, CV_32S, CV_32F, and CV_64F element
   --  value domains used by typed Mat accessors and shared numeric
   --  APIs. Float16 remains Core-specific.
   subtype UInt8_Value is Interfaces.Unsigned_8;
   subtype Int8_Value is Interfaces.Integer_8;
   subtype UInt16_Value is Interfaces.Unsigned_16;
   subtype Int16_Value is Interfaces.Integer_16;
   subtype Int32_Value is Interfaces.Integer_32;
   subtype Float32_Value is Interfaces.IEEE_Float_32;
   subtype Float64_Value is Interfaces.IEEE_Float_64;

   type Size_Coordinate is
     new Interfaces.Integer_32 range 0 .. Interfaces.Integer_32'Last;

   type Point_Coordinate is new Interfaces.Integer_32;

   type Size is record
      Width  : Size_Coordinate := 0;
      Height : Size_Coordinate := 0;
   end record;

   type Point is record
      X : Point_Coordinate := 0;
      Y : Point_Coordinate := 0;
   end record;

   --  A zero-based, value-semantic sequence of points. An empty result has
   --  the null range 1 .. 0.
   type Point_Array is array (Natural range <>) of Point;

   --  Axis-aligned rectangle with a signed origin and nonnegative size.
   --  OpenCV rectangle origins may be negative. Width and Height remain
   --  nonnegative in this Ada value model. A Rect is not restricted merely
   --  because Mat ROI operations require nonnegative origins; Mat.Region
   --  enforces that ROI-specific constraint itself.
   type Rect is record
      X      : Point_Coordinate := 0;
      Y      : Point_Coordinate := 0;
      Width  : Size_Coordinate := 0;
      Height : Size_Coordinate := 0;
   end record;

   --  Value-semantic 2-D point with binary32 coordinates. This is the
   --  shared representation for OpenCV floating-point 2-D points.
   type Float32_Point is record
      X : Float32_Value := 0.0;
      Y : Float32_Value := 0.0;
   end record;

   --  Value-semantic two-dimensional binary32 extent. Individual operations
   --  define whether negative dimensions are meaningful.
   type Float32_Size is record
      Width  : Float32_Value := 0.0;
      Height : Float32_Value := 0.0;
   end record;

   --  Value-semantic rotated rectangle with binary32 native OpenCV fields.
   --  Angle_Degrees is deliberately not normalized because different OpenCV
   --  operations and versions can use distinct equivalent representations.
   type Rotated_Rect is record
      Center        : Float32_Point := (X => 0.0, Y => 0.0);
      Size          : Float32_Size := (Width => 0.0, Height => 0.0);
      Angle_Degrees : Float32_Value := 0.0;
   end record;

   type Scalar is record
      Component_0 : Long_Float := 0.0;
      Component_1 : Long_Float := 0.0;
      Component_2 : Long_Float := 0.0;
      Component_3 : Long_Float := 0.0;
   end record;

   function Make_Scalar
     (Component_0 : Long_Float;
      Component_1 : Long_Float := 0.0;
      Component_2 : Long_Float := 0.0;
      Component_3 : Long_Float := 0.0) return Scalar
   is (Component_0 => Component_0,
       Component_1 => Component_1,
       Component_2 => Component_2,
       Component_3 => Component_3);

   type Border_Kind is
     (Constant_Border, Replicate, Reflect, Reflect_101, Wrap);

   type Angle_Unit is (Radians, Degrees);

end OpenCV;
