procedure Ambiguous is
   type First is range 0 .. 10;
   type Second is range 0 .. 10;
   function Pick (Value : First) return Integer is (1);
   function Pick (Value : Second) return Integer is (2);
   X : Integer := Pick (1);
begin
   null;
end Ambiguous;