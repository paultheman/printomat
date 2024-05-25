import tkinter as tk
from tkinter import ttk
from logger import logger
from pdftools import PDFConverter
from typing import List
from constants import *



class Cells(ttk.Entry):
    """ Cells class with a length of RAND_SEQ_LENGTH.
    """

    counter = 0 # needed to create unique names for each cell

    def __init__(self, no_of_cells:int):
        self.no_of_cells = no_of_cells
        self.cell_list: list = []
        self.entry_values: list = [' '] * no_of_cells
        self.string_to_match = tk.StringVar()


    def create(self, frame:tk.Frame, row: int) -> None:
        """ Creates the cells widget
        """
        for no in range(self.no_of_cells):
            self.cell = ttk.Entry(frame, font=("Helvetica", 80), width=2, justify='center', name=f'cell_{Cells.counter}_{no}', validate='key',
                             validatecommand=(frame.register(lambda new_value: False if len(new_value) >1 else True), '%P'))
            self.cell.grid(row=row, column=no, padx=5, pady=5)
            self.cell_list.append(self.cell)
            if DEBUG is True:
                self.cell.bind('<KeyPress>', self._set_focus) # needed only for physical keyboard input
            self.cell.bind('<FocusOut>', self._get_entry_value)
        Cells.counter+=1
        self.cell_list[0].focus()


    def _get_entry_value(self, event: tk.Event) -> None:
        """ Sets a tk.StringVar() when all the cells are filled. 
        """
        entry_index = int(event.widget.winfo_name()[-1])
        t_val = event.widget.get()
        if t_val != self.entry_values[entry_index]:
            self.entry_values[entry_index] = t_val
            if all(x.isalnum() for x in self.entry_values):
                self.string_to_match.set(''.join(self.entry_values))                 


    def _set_focus(self, event: tk.Event) -> None:
        """ Moves focus on the next cell when physicall input is given.
            !! Not needed when input comes from OnScreen Keyboard class.
        """
        if event.keysym not in ['BackSpace', 'Delete']:
            event.widget.tk_focusNext().focus()
            event.widget.delete(0, tk.END)



class Keyboard(ttk.Button):
    """ On screen keyboard with numbers and letters.
    """
    keyboard_rows:list = [
                ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
                ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
                ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
                ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
                ]
    col_span: int = 1


    def __init__(self, master:ttk.Frame, row_i:int, **kw):        
        for row in self.keyboard_rows:
            for key_i, key in enumerate(row):
                super().__init__(master, text=key, width=5, command= lambda key=key: self._write_to_entry(key), 
                                    takefocus=0, style='Accent.TButton')
                self.grid(row=row_i, column=key_i, ipady=10, padx=3, pady=3, columnspan=self.col_span)
            row_i += 1
            self.col_span += 1


    def _write_to_entry(self, key: str) -> None:
        """ Places a character in a focused widget.
        """

        focused_widget = tk.Tk.focus_get(self)
        #if isinstance(focused_widget, ttk.Entry):
        focused_widget.delete(0, tk.END)
        focused_widget.insert(0, key)
        focused_widget.tk_focusNext().focus()



class ClearBtn(ttk.Button):
    """ Creates the Clear ALL button 
    """
    def __init__(self, master:ttk.Frame, **kw):
        super().__init__(master, takefocus=0, **kw)

    
    def clear_all_cells(self, cells: Cells) -> None:
        """ Callback function for the Clear ALL button.
            Deletes the cell entries.
        """
        for i in range(len(cells.cell_list)):
            cells.cell_list[i].delete(0, tk.END)
            cells.entry_values[i] = ' '
        cells.cell_list[0].focus()


    def clear_cell(self, cells:Cells) -> None:
        """ Callback function for the Clear button.
            Deletes one cell entry.
        """
        focused_cell_i = int(str(cells.cell.focus_get())[-1])
        cell_value = cells.cell_list[focused_cell_i].get()
        if cell_value == '':
            cells.cell_list[focused_cell_i-1].focus_set()
            cells.cell_list[focused_cell_i-1].delete(0, tk.END)    
        else:
            cells.cell_list[focused_cell_i].delete(0, tk.END)



class FileOptions:
    """ Stores the doc options/settings """
    
    def __init__(self, pdf_obj:PDFConverter) -> None:
        
        self.pdf_obj = pdf_obj
        
        self.no_copies:int = 1
        self.color:str = 'Color'
        self.both_sides:str = 'Print both sides'
        self.orientation:str = 'Portrait' if self.pdf_obj.get_orientation() == 'P' else 'Landscape'
        # self.scale:str = '100%'
        self.layout:int = 1



class FileListbox(ttk.Treeview):
    """ Creates the FileList (Treeview) widget that holds the
        list of files found in folder.
    """

    available_selection = {'current', 'previous'}

    def __init__(self, master:ttk.Frame, files_list:list, entry_dir:str, fileOptions:List[FileOptions], **kw):

        super().__init__(master, selectmode='none', columns=("Files", "Type"), show='', **kw)

        self.entry_dir = entry_dir
        self.fileOptions = fileOptions

        self.heading("Files", text = 'Files', anchor=tk.CENTER, )
        self.heading("Type", text='Type', anchor=tk.CENTER)
        self.column('Files', stretch=tk.YES, anchor='w')
        self.column('Type', stretch=tk.YES, width=50, anchor='center')
                
        self._populate_list(files_list)
    
        self.bind("<ButtonRelease-1>", self._select_deselect_item)

        self.no_sel_itm = tk.IntVar()       # no. of items selected


    @property
    def new_selection(self):
        return self.focus()
    
    @property
    def prev_selection(self):
        return self.selection()[-1]
        

    def selected_item_index(self, selection:str) -> int:
        """ Returns the index of the selected item.
        """

        if selection == 'current':
            return int(self.new_selection)
        elif selection == 'previous':
            return int(self.prev_selection)
        else:
            raise ValueError(f"'type' must be one of {self.available_selection}")


    def selected_item(self, selection:str) -> str:
        """ Returns the complete file name (with extenstion) 
            of the currently/previously selected item.
            Args: selection: 'current' or 'previous'
        """

        if selection == 'current':
            return self.item(self.new_selection)['text']
        elif selection == 'previous':
            return self.item(self.prev_selection)['text']
        else:
            raise ValueError(f"'type' must be one of {self.available_selection}")


    def selected_item_name(self, selection:str) -> str:
        """ Returns ONLY the file name (without extension)
            of the currently/previously selected item.
            Args: selection: 'current' or 'previous'
        """
 
        if selection == 'current': 
            return self.item(self.new_selection)['values'][0]
        elif selection == 'previous':
            return self.item(self.prev_selection)['values'][0]        
        else:
            raise ValueError(f"'type' must be one of {self.available_selection}")  


    def _select_deselect_item(self, event:tk.Event) -> None:
        """ Callback function, selects/deselects the item 
            and increases selected files counter.
        """

        if self.focus() not in self.selection():
            self.selection_add(self.new_selection)
        else:
            self.selection_remove(self.new_selection)

            if len(self.selection()) > 0:
                self.focus(self.prev_selection)

        self.no_sel_itm.set(len(self.selection()))


    def _populate_list(self, files_list:list) -> None:
        """ Populates the FileListbox with the files found in folder.
        """

        # if an exception occurs we keep the iterator consecutive
        exceptions = 0
        
        for file_i, file in enumerate(files_list):

            try:
                pdf_obj = PDFConverter(self.entry_dir, file)

                if pdf_obj.get_f_ext != 'pdf':
                    log_str = f'Starting img to pdf conversion for file \'{file}\' ... '
                    pdf_obj.convert_image_w_pmargin()

                else:
                    log_str = f'Starting pdf to pdf conversion for file \'{file}\' ... '
                    pdf_obj.check_and_resize_pdf()

                log_str += 'Done'

            except Exception as e:
                log_str += repr(e)
                exceptions += 1

            else:
                # Insert the file in the FileListbox
                self._insert(pdf_obj, file_i-exceptions, file)

                # Create the fileOptions required for this file index
                self.fileOptions.insert(file_i-exceptions, FileOptions(pdf_obj))                

            logger.debug(log_str)


    def _insert(self, pdf_obj:PDFConverter, file_i:int, file:str) -> str:
        """ Inserts the PDF document into the FileList. The matching filename must have a .1 at the end.
        """
    
        return self.insert('', 'end', values=(pdf_obj.get_f_name, pdf_obj.get_f_ext.upper()), iid=file_i, text=file + '.1')
       


class PageBtn(ttk.Button):
    """ Creates the Prev/ Next PDF page button 
    """
    def __init__(self, master:ttk.Frame, **kw):
        super().__init__(master, takefocus=0, **kw)


    def next_page(self, pdf_obj:PDFConverter) -> None:
        current_page = pdf_obj.current_page.get()
        if (current_page < pdf_obj.page_count - 1):
            pdf_obj.current_page.set(current_page + 1)


    def prev_page(self, pdf_obj:PDFConverter) -> None:
        current_page = pdf_obj.current_page.get()
        if (current_page > 0):
            pdf_obj.current_page.set(current_page - 1)



class NoCopiesBtn(ttk.Button):
    """ Increases the copies no. for FileOptions 
    """

    def __init__(self, master:ttk.Frame, **kw):
        super().__init__(master, takefocus=0, **kw)

    def increse(self, fileOptions:List[FileOptions], index:int, tk_var:tk.IntVar) -> None:
        if fileOptions[index].no_copies < 99:
            fileOptions[index].no_copies += 1
            tk_var.set(fileOptions[index].no_copies)

    def decrease(self, fileOptions:List[FileOptions], index:int, tk_var:tk.IntVar) -> None:
        if fileOptions[index].no_copies > 1:
            fileOptions[index].no_copies -= 1
            tk_var.set(fileOptions[index].no_copies)



# class ScaleBtn(ttk.Button):
#     """ Increases the scale for FileOptions 
#     """

#     def __init__(self, master:ttk.Frame, **kw):
#         super().__init__(master, takefocus=0, **kw)

#     def increse(self, fileOptions:List[FileOptions], index:int, tk_var:tk.IntVar) -> None:
#         if fileOptions[index].no_copies < 150:
#             fileOptions[index].no_copies += 10
#             tk_var.set(fileOptions[index].no_copies)

#     def decrease(self, fileOptions:List[FileOptions], index:int, tk_var:tk.IntVar) -> None:
#         if fileOptions[index].no_copies > 50:
#             fileOptions[index].no_copies -= 10
#             tk_var.set(fileOptions[index].no_copies)

