import tkinter as tk
from tkinter import ttk
from rand import RAND_SEQ_LENGTH, ENTRIES_FPATH
from logger import logger
import os
from PIL import Image, ImageTk, ImageOps
from guielements import *
from pdftools import PDFModifier



FILE_TYPES = ['.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp', '.gif']


class App(tk.Tk):
    INACTIVITY_LIMIT = 20 * 1000    # milliseconds
    MAX_TRIES_TIMEOUT = 10          # seconds
    MAX_TRIES = 10                  # maximum tries to enter a string
    C_WIDTH = 500                   # preview tk.Canvas width
    C_HEIGHT = 500                  # preview tk.Canvas height
    W_WIDTH = 1024                  # window width
    W_HEIGHT = 600                  # window height


    def __init__(self, **kw):
        super().__init__(**kw)         

        self.title("Printomat")
        self.theme = "park"
        self.theme_path = os.path.join('..', 'themes', self.theme.lower(), self.theme.lower() + '.tcl')
        self.tk.call("source", self.theme_path)
        self.tk.call("set_theme", "dark")
    
        self.style = ttk.Style(self)
        self.style.configure('Accent.TButton', font=('Helvetica', 20))
        self.style.configure('Clear.TButton', font=('Helvetica', 20))
        self.style.configure('ClearAll.TButton', foreground='darkgrey', font=('Helvetica', 15))
        self.style.configure('Page.TButton', font=('Helvetica', 15))
        self.style.configure('Treeview.Heading', font=('Helvetica', 18), rowheight=30)
        self.style.configure('Treeview', font=('Helvetica', 18), rowheight=30)
        self.style.configure('Options.TButton', font=('Helvetica', 15))
        self.style.configure('Switch.TCheckbutton', font=('Helvetica', 18))
        self.style.configure('Options.TRadiobutton', font=('Helvetica', 18))
        self.style.configure('Listbox', font=('Helvetica',18))

        # https://stackoverflow.com/a/15463496
        # https://stackoverflow.com/a/28940421
        import tkinter.font as tkFont
        list_box_font = tkFont.nametofont("TkTextFont")
        list_box_font.configure(size=24)
        self.option_add("*TCombobox*Listbox*Font", list_box_font)


        self.tries = 0
        self.timer_flag:str = None
        self.entry_dir:str = None
        self.prev_no_sel_itm:int = 0
        
        self.pdf_obj:PDFModifier = None        
        
        self.fileOptions:List[FileOptions] = []

        self.f_selected: str = None
        self.f_name:str = None
        self.f_iid:int = None

        self.no_copies = tk.IntVar()            # no of copies
        self.color = tk.StringVar()             # 'color' and 'bw'
        self.both_sides = tk.StringVar()        # 1 = both sides, 0 = one side
        self.orientation = tk.StringVar()       # 'Portrait' or 'Landscape'
        # self.scale = tk.StringVar()           # 50 - 150
        self.layout = tk.IntVar()               # pages per sheet

        self.options_updated = tk.IntVar()      # options updated
        self.options_updated.trace_add('write', lambda *args: self.preview_file())

        self.bind_all('<Button-1>', self.reset_timer)

        self.first_screen()
        
        self.eval('tk::PlaceWindow . center')
        self.geometry(f"{App.W_WIDTH}x{App.W_HEIGHT}")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.mainloop()


    def reset_timer(self, event = None):
        """ Callback function on every Left mouse Button.
        """

        if self.timer_flag is not None:
            self.after_cancel(self.timer_flag)
        self.timer_flag = self.after(App.INACTIVITY_LIMIT, self.user_is_inactive)


    def user_is_inactive(self):
        """ Function that is called when the user is inactive after App.timer expires.
        """

        logger.info('Inactivity timeout %s reached.' % App.INACTIVITY_LIMIT)
        self.first_screen()


    def first_screen(self) -> None:
        """ First screen that is displayed to the user.
            Creates the Cells and Keyboard objects.
        """

        # Destroy previous widgets so we have a clean interface when timeout occurs
        self.destroy_all_widgets()
        self.pdf_obj = None
        self.tries = 0
        
        self.top_container = ttk.Frame(self)
        self.top_container.grid(row = 0, column = 0)

        self.cellsFrame = ttk.Frame(master=self.top_container)
        self.cellsFrame.grid(row=0, column=0, sticky='S')
        self.cellsLabel = ttk.Label(master=self.cellsFrame, text = 'Enter the code you recieved in the cells below:', 
                               font=("Helvetica", 30), justify='center')
        self.cellsLabel.grid(row=0, column=0, columnspan=RAND_SEQ_LENGTH, pady=(30, 12))

        self.cells = Cells(RAND_SEQ_LENGTH)
        self.cells.create(self.cellsFrame, row=1)
        self.cells.string_to_match.trace_add('write', lambda *args: self.search_match(self.cells, self.cellsFrame))        

        self.clearBtnFrame = ttk.Frame(master=self.top_container)
        self.clearBtnFrame.grid(row=1, column=0, columnspan=RAND_SEQ_LENGTH)

        self.clearBtn = ClearBtn(master=self.clearBtnFrame, text='←', command= lambda: self.clearBtn.clear_cell(self.cells),
                               style='Clear.TButton')
        self.clearBtn.grid(row=0, column=0, ipady=2, padx=3, pady=(30, 5))

        self.clearAllBtn = ClearBtn(master=self.clearBtnFrame, text='Clear ALL', command= lambda: self.clearAllBtn.clear_all_cells(self.cells),
                               style='ClearAll.TButton',)
        self.clearAllBtn.grid(row=0, column=1, ipadx=20, padx=3, ipady=5, pady=(30, 5))

        self.keyboardFrame = ttk.Frame(master=self.top_container)
        self.keyboardFrame.grid(row=2, column=0, sticky='N')
        self.kbd = Keyboard(master=self.keyboardFrame, row_i=0)


    def second_screen(self) -> None:
        """ Second screen that is accessed if an imput string is equal to a folder name.
        """

        self.destroy_all_widgets()

        self.top_container = ttk.Frame(self)
        self.top_container.grid(row = 0, column = 0)

        self.fileList_column = ttk.Frame(master=self.top_container)
        self.preview_column = ttk.Frame(master=self.top_container)
        self.fileOptions_column = ttk.Frame(master=self.top_container) 
        self.fileList_column.grid(column=0, row = 0, padx=(0, 5))
        self.preview_column.grid(column=1, row=0)
        self.fileOptions_column.grid(column=2, row=0, padx=(5, 0))

        self.fileList_container = ttk.Frame(master=self.fileList_column)
        self.fileList_container.grid(row = 0, column=0)

        self.fileList = FileListbox(self.fileList_container, self.files_found, self.entry_dir, 
                                    self.fileOptions, height = 6)
        self.fileList.grid(column=0, row=0)
        self.fileList.update_idletasks()
 
        self.fileList.no_sel_itm.trace_add('write', lambda *args: self.preview_file())
                                                                               
        self.scrollbar = ttk.Scrollbar(master=self.fileList_container, orient= 'vertical', command=self.fileList.yview)
        self.scrollbar.grid(column=1, row=0, sticky='NS')
        self.fileList.configure(yscrollcommand=self.scrollbar.set)

        self.print_btn = ttk.Button(master=self.fileList_container, style='Accent.TButton', 
                                    text='No documents selected', state='disabled')
        self.print_btn.grid(column=0, row=1, columnspan=2, sticky='NSEW', pady=10)

        self.exit_btn = ttk.Button(master=self.fileList_container, style='Clear.TButton',
                                   text='Exit', command=self.first_screen)
        self.exit_btn.grid(column=0, row = 2, columnspan=2, sticky='NSEW')

        self.docFrame = ttk.Frame(master=self.preview_column)
        self.docFrame.grid(row=0, column=0)

        self.docTitle = ttk.Label(master=self.docFrame, justify='center', font=('Helvetica', 18))
        self.docTitle.grid(row=0, column=0, columnspan=3, pady=(10, 5))
        
        self.canvas = tk.Canvas(master=self.docFrame, width=App.C_WIDTH, height=App.C_HEIGHT)
        self.canvas.grid(row=1, column=0, columnspan=3)
        self.canvas_default()

        self.doc_buttons_container = ttk.Frame(master=self.preview_column)
        self.doc_buttons_container.grid(column=0, row=2)
        self.prev_page_btn = PageBtn(master=self.doc_buttons_container, text='◀︎', width=1, style='Page.TButton')
        self.next_page_btn = PageBtn(master=self.doc_buttons_container, text='▶︎', width=1, style='Page.TButton')
        self.prev_page_btn.grid(row=0, column=0, sticky='E', pady=5, padx=(0, 40), ipadx=5, ipady=5)
        self.next_page_btn.grid(row=0, column=2, sticky='W', pady=5, padx=(40, 0), ipadx=5, ipady=5)
        self.prev_page_btn.grid_remove()
        self.next_page_btn.grid_remove()
        
        self.page_label = ttk.Label(master=self.doc_buttons_container, font=('Helvetica', 16))
        self.page_label.grid(column=1, row=0)
        self.page_label.grid_remove()


        ### Definitions of the FileOptions widgets

        f = ttk.Frame(relief='flat')            # see https://stackoverflow.com/a/12482468
        self.options_container = ttk.Labelframe(master=self.fileOptions_column, labelwidget=f)
        self.options_container.grid(column=0, row=0, sticky='NSEW')

        self.copies_container = ttk.Frame(master=self.options_container)
        self.copies_container.grid(column=0, row=0, sticky='NSEW')
        self.copies_label = ttk.Label(master=self.copies_container, text='Copies', font=('Helvetica', 18), style='Options.TLabel')
        self.copies_label.grid(row=0, column=0, sticky='W', padx=(5, 0))
        self.copies_no = ttk.Label(master=self.copies_container, textvariable=self.no_copies, font=('Helvetica', 18), background='grey', 
                                   anchor='center', width=2)
        self.copies_no.grid(row=0, column=1, sticky='E', padx=10, ipady=4, ipadx=3)
        self.copies_dec_btn = NoCopiesBtn(master=self.copies_container, text='-', width=1, style='Options.TButton', 
                                     command= lambda: self.copies_dec_btn.decrease(self.fileOptions, self.f_iid, self.no_copies))
        self.copies_dec_btn.grid(column=2, row=0, sticky='E')
        self.copies_inc_btn = NoCopiesBtn(master=self.copies_container, text='+', width=1, style='Options.TButton', 
                                     command= lambda: self.copies_inc_btn.increse(self.fileOptions, self.f_iid, self.no_copies))
        self.copies_inc_btn.grid(column=3, row=0, sticky='E', padx=(5, 5), pady=7)

        self.switches_container = ttk.Frame(master=self.options_container)
        self.switches_container.grid(column=0, row=1, sticky='NSEW')
        self.color_sw = ttk.Checkbutton(master=self.switches_container, style='Switch.TCheckbutton', variable=self.color,
                                        textvariable=self.color, offvalue='Grayscale', onvalue='Color', command=self.set_color)
        self.color_sw.grid(column=0, row=0, sticky='W', pady=7)
        self.both_sides_sw = ttk.Checkbutton(master=self.switches_container, style='Switch.TCheckbutton', variable=self.both_sides,
                                             textvariable=self.both_sides, offvalue='Print one side', onvalue='Print both sides')
        self.both_sides_sw.grid(column=0, row=1, sticky='W', pady=7)
        self.orientation_sw = ttk.Checkbutton(master=self.switches_container, style='Switch.TCheckbutton', variable=self.orientation,
                                              offvalue='Landscape', onvalue='Portrait', textvariable=self.orientation, command=self.set_orientation)
        self.orientation_sw.grid(column=0, row=2, sticky='W', pady=7)
        
        # self.scaling_container = ttk.Frame(master=self.options_container)
        # self.scaling_container.grid(column=0, row=2, sticky='NSEW')
        # self.scale_label = ttk.Label(master=self.scaling_container, text='Scale', font=('Helvetica', 18))
        # self.scale_label.grid(column=0, row=0, pady=7, sticky='W', padx=(5,0))
        # self.scale_percent = ttk.Label(master=self.scaling_container, textvariable=self.scale, font=('Helvetica', 18), background='grey', 
        #                                anchor='center', width=4)
        # self.scale_percent.grid(row=0, column=1, sticky='E', padx=5, ipady=4, ipadx=3)
        # self.scale_inc_btn = ScaleBtn(master=self.scaling_container, text='-', width=1, style='Options.TButton')
        # self.scale_inc_btn.grid(column=2, row=0, sticky='E')
        # self.scale_dec_btn = ScaleBtn(master=self.scaling_container, text='+', width=1, style='Options.TButton')
        # self.scale_dec_btn.grid(column=3, row=0, sticky='E', padx=(5, 5), pady=7)

        self.layout_container = ttk.Frame(master=self.options_container)
        self.layout_container.grid(column=0, row=3, sticky='NSEW')
        self.layout_label = ttk.Label(master=self.layout_container, text='Page layout', font=('Helvetica', 18))
        self.layout_label.grid(column=0, row=0, pady=7, padx=5)
        self.layout_combo = ttk.Combobox(master=self.layout_container, values=['1', '2', '4'], textvariable=self.layout,
                                    font=('Helvetica', 18), width=2, state='readonly')
        self.layout_combo.bind("<<ComboboxSelected>>", self.set_layout)
        self.layout_combo.grid(column=1, row=0, pady=7, padx=(12, 0))

        self.buttons_container = ttk.Frame(master= self.fileOptions_column, width=100)
        self.buttons_container.grid(column=0, row=1, sticky='NSEW', pady=10)
        self.reset_btn = ttk.Button(master = self.buttons_container, style='Clear.TButton', 
                                    text='Restore original', command= self.reset_doc, width=14)
        self.reset_btn.grid(column=0, row=0)

        # Disable all fileOptions for the first display (no files are selected)
        self.c_state(self.fileOptions_column, 'disabled')


    def preview_file(self, pdf_is_modified = False, reset_pdf = False) -> None:
        """ Displays a preview of the selected file in a tk.Canvas.
        """

        no_sel_itm = self.fileList.no_sel_itm.get()

        # if at least a file is selected
        if (no_sel_itm > 0):

            # if a new file is selected
            if (no_sel_itm  >= self.prev_no_sel_itm):
                self.f_selected = self.fileList.selected_item('current')
                self.f_name = self.fileList.selected_item_name('current')
                self.f_iid = self.fileList.selected_item_index('current')

            # if a file is deselected
            else:
                # if another file has been deselected than the one in focus
                # delete the pdf_obj so that it can be saved and its new name updated in fileList
                #if pdf_is_modified is False:
                if pdf_is_modified is False and self.pdf_obj is not None:
                    self.pdf_obj.__del__(increase_extension=True)
                self.f_selected = self.fileList.selected_item('previous')
                self.f_name = self.fileList.selected_item_name('previous')
                self.f_iid = self.fileList.selected_item_index('previous')

            # create a new PDF object only if one does not yet exist
            # otherwise we will use the one already created and display the changes
            if pdf_is_modified is False:
                # make sure we call the destructor!! __del__ is not automatically called
                if self.pdf_obj is not None:
                    if reset_pdf == True:
                        self.pdf_obj.__del__(increase_extension=False)
                    else:
                        self.pdf_obj.__del__(increase_extension=True)
                self.pdf_obj = PDFModifier(self.entry_dir, self.f_selected, self.fileList)
                if reset_pdf == True:
                    self.fileOptions[self.f_iid].__init__(self.pdf_obj)


            if (self.pdf_obj.page_count) > 1:
                self.pdf_obj.current_page.trace_add('write', lambda *args: self.preview_page())
                self.prev_page_btn.configure(command = lambda: self.prev_page_btn.prev_page(self.pdf_obj))
                self.next_page_btn.configure(command = lambda: self.next_page_btn.next_page(self.pdf_obj))
                self.prev_page_btn.grid()
                self.next_page_btn.grid()
                self.page_label.grid()

            else:
                self.prev_page_btn.grid_remove()
                self.next_page_btn.grid_remove()
                self.page_label.grid_remove()

            # Configure document title label to max 35 chars
            self.docTitle.configure(text = self.f_name[:35] + (self.f_name[35:] and '...'))
            self.print_btn.configure(text=f'Print {no_sel_itm} documents', state='enabled')

            self.no_copies.set(self.fileOptions[self.f_iid].no_copies)
            self.color.set(self.fileOptions[self.f_iid].color)
            self.both_sides.set(self.fileOptions[self.f_iid].both_sides)
            self.orientation.set(self.fileOptions[self.f_iid].orientation)
            # self.scale.set(self.fileOptions[self.f_iid].scale)
            self.layout.set(self.fileOptions[self.f_iid].layout)

            self.preview_page()
            self.c_state(self.fileOptions_column, 'enabled')
            self.prev_no_sel_itm = no_sel_itm

        else:
            # destroy the pdf object only if it is assgined
            if self.pdf_obj is not None:    
                # if the only document has been deselected delete the obj so it can be saved locally
                self.pdf_obj.__del__(increase_extension=True)

            self.docTitle.configure(text='')
            self.page_label.grid_remove()
            self.prev_page_btn.grid_remove()
            self.next_page_btn.grid_remove()
            self.print_btn.configure(text='No document slected', state='disabled')
            self.canvas_default()
    

    def preview_page(self) -> None:
        """ Displays the current page in the Canvas
        """

        self.page_label.configure(text=f'Page {self.pdf_obj.current_page.get() + 1} / {self.pdf_obj.page_count}')
        
        img:Image.Image = self.pdf_obj.create_img_from_pdf()

        if self.color.get() == "Grayscale":
            img = ImageOps.grayscale(img)

        img.thumbnail((App.C_WIDTH, App.C_HEIGHT), Image.LANCZOS)

        self.tkimg = ImageTk.PhotoImage(img)        # 'tkimg' is garbage collected after function finishes, self is needed
        self.canvas.create_image(App.C_WIDTH/2 + 2, App.C_HEIGHT/2 + 2, anchor=tk.CENTER, image=self.tkimg)


    def canvas_default(self) -> None:
        """ Creates a Canvas used no files are selected.
        """

        self.canvas.delete('all')
        # canvas.configure(bg='systemWindowBackgroundColor')
        self.canvas.create_text(int(App.C_WIDTH/2), 170, anchor=tk.CENTER, text='🖨️', font =('Helvetica', 80))
        self.canvas.create_text(int(App.C_WIDTH/2), 250, anchor=tk.CENTER, text='Select the files to print', font =('Helvetica', 30))
        self.canvas.create_text(int(App.C_WIDTH/2), 300, anchor=tk.CENTER, text='and preview', font =('Helvetica', 30))
        
        # disable FileOptions when no files are selected
        self.c_state(self.fileOptions_column, 'disabled')


    def reset_doc(self):
        """ Resets the pdf document to the original state. """

        # se the 'text' option of the FileListbox to the initial value ending in .1
        self.fileList.item(self.f_iid, text = self.pdf_obj.get_f_name + '.1')

        # preview the file with the 'reset_pdf' as True
        self.preview_file(reset_pdf = True)
        

    def c_state(self, frame:ttk.Frame, state:str = 'disabled') -> None:
        """ Enables/Disables all widgets from a ttk.Frame recursively.
            Args: state:str : 'enabled' or 'disabled'
        """

        for widget in frame.winfo_children():
            if isinstance(widget, (ttk.Frame, ttk.Labelframe)):
                self.c_state(widget, state)
            else:
                if isinstance(widget, ttk.Combobox):
                    widget.configure( state = 'readonly' if state == 'enabled' else 'disabled')
                else:
                    widget.configure(state=state)


    def set_orientation(self):
        
        if self.orientation.get() == "Landscape":
            self.pdf_obj.rotate_pages('L')
        else:
            self.pdf_obj.rotate_pages('P')

        self.fileOptions[self.f_iid].orientation = self.orientation.get()

        self.preview_file(pdf_is_modified=True)


    def set_color(self):
        """ Sets the color for the specific document and the displays the page.
        """
        
        self.fileOptions[self.f_iid].color = self.color.get()
        self.preview_page()


    def set_layout(self, event:tk.Event):
        """ Sets the number of pages per sheet
        """
        
        # disable the selection of text for aesthetics
        self.layout_combo.selection_clear()

        self.fileOptions[self.f_iid].layout = self.layout.get()
        self.layout.set(self.fileOptions[self.f_iid].layout)

        self.pdf_obj.multiple_pages(self.layout.get())

        self.fileOptions[self.f_iid].orientation = ('Landscape'
            if self.pdf_obj[0].rect.width > self.pdf_obj[0].rect.height
            else 'Portrait')        
        self.orientation.set(self.fileOptions[self.f_iid].orientation)

        self.pdf_obj.current_page.set(0)
        self.preview_file(pdf_is_modified=True)


    def search_match(self, cells:Cells, frame:ttk.Frame) -> None:
        """ After all the cells are filled searches for a matching folder.
            If no folder is found self.tries is increased. If tries reaches its limit,
            we disable the cells, show a message and wait for the inactivity callback
            function to restore the first_screen().
        """

        match_str = cells.string_to_match.get()
        logger.info('Got new string to match -> \'%s\'' % match_str)

        if self.tries < App.MAX_TRIES:
            logger.debug('Entry tries: \'%s\'' % self.tries)
            self.entry_dir = os.path.join(ENTRIES_FPATH, match_str)
            self.files_found = []
            
            if os.path.isdir(self.entry_dir):

                self.tries = 0
                logger.debug('Accessing entry -> \'%s\'' % match_str)

                for file in os.listdir(self.entry_dir):

                    abs_path = os.path.join(self.entry_dir, file)
                    if any(file.endswith(ext) for ext in FILE_TYPES):
                        if not os.path.islink(abs_path) and not os.path.isdir(abs_path):
                            self.files_found.append(file)

                logger.info('Files found: %s' % self.files_found)

                self.second_screen()

            else:
                self.tries += 1 
                logger.debug('Entry not found -> \'%s\'' % match_str)
        else:
            logger.info('Max no of tries exceeded') 

            tries_label = ttk.Label(frame, font=('Helvetica', 30), foreground = 'dark orange')
            tries_label.grid(column=0, row=2, columnspan=RAND_SEQ_LENGTH, pady=(15, 0))
            
            self.c_state(frame, 'disabled')
            self.tries_countdown(App.MAX_TRIES_TIMEOUT, frame, tries_label)


    def tries_countdown(self, count, frame:ttk.Frame, label:ttk.Label) -> None:
        label.configure(text = f'Maximum number of tries exceeded, please wait {count} seconds')
        if count:
            count -= 1
            self.after(1000, lambda: self.tries_countdown(count, frame, label))
        else:
            self.c_state(frame, 'enabled')
            label.grid_remove()
            self.tries = 0


    def destroy_all_widgets(self) -> None:
        """ Clean slate.
        """

        for widget in self.winfo_children():
            widget.destroy()
            

if __name__ == "__main__":
    App()