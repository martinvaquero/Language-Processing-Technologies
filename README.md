# Language-Processing-Technologies

Using lark implement a parser for the definition of struct in C language. Consider the following syntax for the istructions 

- definition of a variable (or variables) as a struct, for instance define x and y as a struct

struct data {    
  int a;    
  float b;    
  char c;    
  double d;    
  int e; 
  } x, y; 
  
- assignments of constant values to some fields of one (or more) defined variable, for instance

x.a = 2; 
x.c = 'c'; 

As output you may print the values assigned to the fields, as for instance 

output: struct x    
  a type int value 2    
  b type float value NULL    
  c type char value c    
  d type double value NULL    
  e type int value NULL 
  
(NULL in case there is no assignment)
