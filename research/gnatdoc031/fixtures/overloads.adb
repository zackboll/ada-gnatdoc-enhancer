package body Overloads is
   function Clone (Self : Mat) return Mat is (Self);
   function Clone (Self : UMat) return UMat is (Self);
   function Pick (Value : Integer) return Integer is (Value);
   function Pick (Value : String) return Integer is (Value'Length);
   function Count (Left : Integer) return Integer is (Left);
   function Count (Left, Right : Integer) return Integer is (Left + Right);
   function Named (Left : Integer; Right : String) return Integer is
     (Left + Right'Length);
   function Named (Left : String; Right : Integer) return Integer is
     (Left'Length + Right);
   function Defaulted (Value : Integer; Extra : Boolean := False) return Integer is
     (Value + Boolean'Pos (Extra));
   function Defaulted (Value : String) return Integer is (Value'Length);
   function Result return Integer is (1);
   function Result return String is ("one");
   function Identity (Value : Item) return Item is (Value);
end Overloads;