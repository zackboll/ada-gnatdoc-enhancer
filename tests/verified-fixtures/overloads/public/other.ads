package Other is
   function Pick (Value : Boolean) return Integer is (Boolean'Pos (Value));
end Other;