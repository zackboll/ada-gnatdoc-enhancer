procedure Default_Ambiguous is
   function Select_Value (Value : Integer) return Integer is (Value);
   function Select_Value
     (Value : Integer; Extra : Boolean := False) return Integer is (Value);
   X : Integer := Select_Value (1);
begin
   null;
end Default_Ambiguous;