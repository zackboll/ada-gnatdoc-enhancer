package Overloads is
   type Mat is tagged null record;
   type UMat is tagged null record;
   function Clone (Self : Mat) return Mat;
   function Clone (Self : UMat) return UMat;
   function Pick (Value : Integer) return Integer;
   function Pick (Value : String) return Integer;
   function Count (Left : Integer) return Integer;
   function Count (Left, Right : Integer) return Integer;
   function Named (Left : Integer; Right : String) return Integer;
   function Named (Left : String; Right : Integer) return Integer;
   function Defaulted (Value : Integer; Extra : Boolean := False) return Integer;
   function Defaulted (Value : String) return Integer;
   function Result return Integer;
   function Result return String;
end Overloads;
