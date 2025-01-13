# Guide to LuaTeXit's tex_compile error codes and their corresponding failure messages


## The Zeros

The Zeros are error codes which relate to the executables that LuaTeXit uses to compile TeX documents. These error codes are not directly related to the TeX document itself, but rather to the executables that LuaTeXit uses to compile the document. These are serious errors that disable the core functionality of LuaTeXit, hence requires immediate attention.

| Error Code | Description | Diagnosis |
| :--- | :--- | :--- |
| 001 | TeX engine not found | LuaTeXit could not find the TeX engine specified in the preferences. |
| 002 | TeX engine not executable | LuaTeXit could not execute the TeX engine specified in the preferences. |
| 003 | Permission denied | LuaTeXit does not have permission to execute the TeX engine specified in the preferences. |
| 004 | |
| 005 | |
| 006 | |
| 007 | |
| 008 | |
| 009 | |

## The Ones

The Ones correspond to errors that arise when a user requests LuaTeXit to compile a TeX document. These are typically captured during the `tex_compile` process in the `core` functionality, but are generally useful in guiding which error image to display to the user.

The hundredth digit indicates the One, tenth digit indicates the engine(`0`: plain, `2`: pdf, `6`: xetex and `7`: luatex), and the final digit indicates the error type.

| Error Code | Description | Diagnosis |
| :--- | :--- | :--- |
| 102 | No PDF produced (plain LuaTeX) | The requested compilation did not produce a PDF file. |
| 104 | Nothing to compile (plain LuaTeX) | The user has requested LuaTeXit to compile a TeX document, but the document is empty. |
| 107 | Compilation timed out (plain LuaTeX) | The requested compilation took too long to complete. |
| 108 | Image processing timed out (plain LuaTeX) | The requested image processing took too long to complete. |
| 122 | No PDF produced (pdfTeX) | The requested compilation did not produce a PDF file. |
| 124 | Nothing to compile (pdfTeX) | The user has requested LuaTeXit to compile a TeX document, but the document is empty. |
| 127 | Compilation timed out (pdfTeX) | The requested compilation took too long to complete. |
| 128 | Image processing timed out (pdfTeX) | The requested image processing took too long to complete. |
| 162 | No PDF produced (XeTeX) | The requested compilation did not produce a PDF file. |l
| 164 | Nothing to compile (XeTeX) | The user has requested LuaTeXit to compile a TeX document, but the document is empty. |
| 167 | Compilation timed out (XeTeX) | The requested compilation took too long to complete. |
| 168 | Image processing timed out (XeTeX) | The requested image processing took too long to complete. |
| 172 | No PDF produced (LuaTeX) | The requested compilation did not produce a PDF file. |
| 174 | Nothing to compile (LuaTeX) | The user has requested LuaTeXit to compile a TeX document, but the document is empty. |
| 177 | Compilation timed out (LuaTeX) | The requested compilation took too long to complete. |
| 178 | Image processing timed out (LuaTeX) | The requested image processing took too long to complete. |
|||