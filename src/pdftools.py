import fitz_old as fitz
from PIL import Image
import os
from logger import logger
import typing
import tkinter as tk
from tkinter import ttk


class PDFConverter(fitz.Document):

    def __init__(self, entry_dir:str, file:str):
       
        self.entry_dir:str = entry_dir                                  # path to /tmp/.. dir
        self.file:str = file                                            # file name with extension
        self.f_path:str = os.path.join(self.entry_dir, self.file)       # complete path to file
        self.current_page = tk.IntVar()
        self.current_page.set(0)
        self.output_pdf_f_path:str = ''                                 # the modified pdf path (saveIncr() can only save once)

        super().__init__(self.f_path)

    
    @property
    def get_f_path(self):
        return self.f_path                                      # complete path to file with file name
    
    @property
    def get_f_name(self):
        return os.path.splitext(self.file)[0]                   # file name w/o extension

    @property
    def get_f_ext(self):
        return (os.path.splitext(self.file)[1])[1:].lower()     # file extension
    
    @property
    def page_count(self):
        return super().page_count


    def convert_image_w_pmargin(self):
        """ Converts image file to A4 PDF doc. Printer margins are added.
        """

        out = fitz.Document()       # opens the out PDF doc

        img = Image.open(self.f_path)                                       # using PIL for because its faster than Pixmap
        img_orientation, img_ratio = self._get_img_orientation(img)         # returns image orientation
        
        page_rect:fitz.Rect = fitz.paper_rect('a4-' + img_orientation)      # set papper size for the PDF in which the image will be inserted to
        page:fitz.Document = out.new_page(width = page_rect.width, height = page_rect.height)       # insert a new blank page in the PDF

        if img_ratio == 1:
            img_rect = fitz.Rect(0, 0, page_rect.width, page_rect.width)
        else:
            img_rect = fitz.Rect(0, 0, page_rect.width, page_rect.height)

        img_rect = self._add_printer_margins(img_rect)

        page.insert_image(filename=self.f_path, rect=img_rect, keep_proportion = True, alpha=0)  # insert the image into the 'out' pdf doc

        self._save_and_close(out)


    def check_and_resize_pdf(self):
        """ Checks if a document of A4 paper size if not it transforms the pages to this format.
        """
        
        out = fitz.Document()

        for page in self:
            page_width = page.rect.width
            page_height = page.rect.height

            if (page_width == 595 and page_height == 842) or (
                page_width == 842 and page_height == 595):
                
                resized_page = out.new_page(width = page_width, height = page_height)
                
            else:
                if page_width > page_height:
                    fmt = fitz.paper_rect('a4-l')
                else:
                    fmt = fitz.paper_rect('a4')
            
                resized_page = out.new_page(width = fmt.width, height = fmt.height)

            rect = self._add_printer_margins(resized_page.rect)
            
            resized_page.show_pdf_page(rect, self, page.number)

        self._save_and_close(out)


    def get_orientation(self) -> str:
        """ Returns a string of the orientation of the fitz.Document.
        """          
        page = self.load_page(0)
        width, height = page.rect.width, page.rect.height
        return 'P' if width <= height else 'L'
        

    def create_img_from_pdf(self) -> Image.Image:
        """ Converts a page from a PDF doc to PIL.Image
        """

        # fitz.TOOLS.store_shrink(10)                           # see https://github.com/pymupdf/PyMuPDF/issues/2588
        
        first_page:fitz.Page = self.load_page(self.current_page.get())
        pix:fitz.Pixmap = first_page.get_pixmap()

        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


    def _save_and_close(self, doc:fitz.Document) -> None:
        
        ext = self._increase_extension()

        path = os.path.join(self.entry_dir, self.get_f_name)
        self.output_pdf_f_path = path + ext

        doc.save(self.output_pdf_f_path)
        doc.close()

    
    def _increase_extension(self) -> str:
        """ Increases the current extension of the document.
        """

        current_ext:str = self.get_f_ext

        try:
            numeric_ext:int = int(current_ext.split('.')[-1])
            numeric_ext += 1
            return ('.' + str(numeric_ext))
        
        except ValueError:
            return ('.' + self.get_f_ext + '.1')
        
        except Exception as e:
            logger.debug(repr(e))


    def _get_img_orientation(self, img:Image.Image) -> typing.Tuple[str, float]:
        orientation = 'P' if img.width <= img.height else 'L'
        ratio = max(img.width, img.height) / min(img.width, img.height)
        return orientation, ratio


    def _add_printer_margins(self, rect:fitz.Rect) -> fitz.Rect:
        return rect + (10, 10, -10, -10) 



class PDFModifier(PDFConverter):
    
    def __init__(self, entry_dir: str, file: str, file_list:ttk.Treeview):
    
        super().__init__(entry_dir, file)
        self.file_list = file_list
        self.orientation:str = self.get_orientation()
        self.counter = 1
        self.transfer_pdf:fitz.Document = None


    @property
    def output_pdf_name(self):
        return os.path.basename(self.output_pdf_f_path)


    def __del__(self, increase_extension = False):
        """ When the doc in memeory is destroyed save it locally and update the
            new name in the Filelistbox object.
        """

        if self.transfer_pdf is not None and increase_extension is True:

            self._save_and_close(self)
            self.transfer_pdf = None

            for child in self.file_list.get_children():
                item = self.file_list.item(child)

                if self.file in item['text']:
                    self.file_list.item(child, text=self.output_pdf_name)
                    break
                
        return super().__del__()


    def rotate_pages(self, rot:str) -> None:
        """ Roates the pages and page content of the doc.
        """

        ## Save original doc
        if self.counter == 1:
            self.first_pdf = self.tobytes()
            self.counter += 1


        if rot != self.orientation:
            self.transfer_pdf = fitz.Document(stream=self.tobytes())
            rect = fitz.paper_rect("a4-" + rot)

        else:
            rect = fitz.paper_rect("a4-" + self.orientation)
            self.transfer_pdf = fitz.Document(stream=self.first_pdf)

        self.delete_pages(0, self.page_count-1)

        for page in self.transfer_pdf:
            newpage = self.new_page(width = rect.width, height = rect.height)
            newpage.show_pdf_page(rect, self.transfer_pdf, page.number, keep_proportion = True)

        self.tobytes(garbage=4)


    def multiple_pages(self, pp_sheet:int) -> None:
        """ Combines multiple pages pdf pages into one. 
        """

        # Load original pdf
        self.transfer_pdf = fitz.Document(os.path.join(self.entry_dir, self.get_f_name + '.1'))
        self.delete_pages(0, self.page_count-1)

        w = self.transfer_pdf[0].rect.br[0]
        h = self.transfer_pdf[0].rect.br[1]

        if pp_sheet == 1:

            for page in self.transfer_pdf:
                newpage = self.new_page(width = page.rect.width, height = page.rect.height)
                newpage.show_pdf_page(page.rect, self.transfer_pdf, page.number)
            return
        
        elif pp_sheet == 2:
            w, h = h, w

            if w < h:
                r1 = fitz.Rect(0, 0, w, h/2) # top rect
                r2 = fitz.Rect(0, h/2, w, h) # bottom rect
            else:
                r1 = fitz.Rect(0, 0, w/2, h) # left rect
                r2 = fitz.Rect(w/2, 0, w, h) # right rect

            r_tab = [r1, r2]

        else: ## pp_sheet == 4
            r1 = self.transfer_pdf[0].rect * 0.5  # top left rect
            r2 = r1 + (r1.width, 0, r1.width, 0)  # top right
            r3 = r1 + (0, r1.height, 0, r1.height)  # bottom left
            r4 = fitz.Rect(r1.br, self.transfer_pdf[0].rect.br)  # bottom right

            r_tab = [r1, r2, r3, r4]

        if self.transfer_pdf.page_count == 1:

            newpage = self.new_page(width = w, height = h)

            # insert same page twice            
            for tab in range(len(r_tab)):
                newpage.show_pdf_page(r_tab[tab], self.transfer_pdf, newpage.number)

        else:
            for page in self.transfer_pdf:
                if page.number % pp_sheet == 0:
                    newpage = self.new_page(width = w, height =h)
                newpage.show_pdf_page(r_tab[page.number % pp_sheet], self.transfer_pdf, page.number)

        self.tobytes(garbage=4)


