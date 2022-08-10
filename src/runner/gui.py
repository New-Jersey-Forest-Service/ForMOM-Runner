import time
import tkinter as tk
from tkinter import filedialog
from tkinter import dialog
import tkinter.ttk as ttk
import attrs
import pathlib
import os
import tempfile
import zipfile
from typing import List, Set, Union

import runner.csv_to_dat as converter
import runner.model_data_classes as model
import runner.pyomo_runner as pyomo_runner
import runner.text as text

import pyomo.environ as pyo
import pyomo.opt as opt

PATH_DISPLAY_LEN = 35
CSV_FILES = [('CSV Files','*.csv'), ('All Files','*.*')]
TXT_FILES = [('Text Files','*.txt'), ('All Files','*.*')]



@attrs.define
class GUIState:
	multipleObjFiles: bool = False
	objFileSingleStr: str = ""
	objFileDirStr: str = ""
	constFileStr: str = ""

	# We store arrays of everything. In the case of a single
	# objective file, we just use the first index
	# TODO: This is bad but tolerable for memory. Analysis lives
	# 		in memory.txt. In the future, we should iterate through
	# 		models so only ever a single one is stored in memory.
	objFilenames: List[str] = None
	loadedModels: List[model.FinalModel] = None
	runInstances: List[pyo.ConcreteModel] = None
	runResults: List[opt.SolverResults] = None






class GuibuildingApp:
	def __init__(self, master=None):
		# state variable
		self.state = GUIState()

		# build ui
		self.im_a_top = master if master else tk.Tk()
		self.frm_title = ttk.Frame(self.im_a_top)
		self.lbl_title = ttk.Label(self.frm_title)
		self.lbl_title.configure(text="ForMOM Linear Model Runner")
		self.lbl_title.pack(anchor="center", expand="true", side="top")
		self.lbl_subtitle = ttk.Label(self.frm_title)
		self.lbl_subtitle.configure(text="Solves linear optimization problems.")
		self.lbl_subtitle.pack(side="top")
		self.frm_title.configure(height=200, width=200)
		self.frm_title.grid(
			column=0, columnspan=3, padx=10, pady=20, row=0, sticky="ew"
		)
		self.frm_actualrunning = ttk.Frame(self.im_a_top)
		self.lblfrm_import = ttk.Labelframe(self.frm_actualrunning)
		self.btn_objcsv = ttk.Button(self.lblfrm_import)
		self.btn_objcsv.configure(text="Objective .csv")
		self.btn_objcsv.grid(column=0, ipadx=2, ipady=2, padx=5, row=1, sticky="ew")
		self.btn_objcsv.configure(command=self.onbtn_import_obj)
		self.btn_constcsv = ttk.Button(self.lblfrm_import)
		self.btn_constcsv.configure(text="Constraint .csv")
		self.btn_constcsv.grid(column=0, ipadx=2, ipady=2, padx=5, row=2, sticky="ew")
		self.btn_constcsv.configure(command=self.onbtn_import_const)
		self.btn_loadmodel = ttk.Button(self.lblfrm_import)
		self.btn_loadmodel.configure(text="Load")
		self.btn_loadmodel.grid(
			column=0, columnspan=2, ipadx=10, ipady=5, padx=10, pady=10, row=3
		)
		self.btn_loadmodel.configure(command=self.onbtn_import_load)
		self.lbl_constpath = ttk.Label(self.lblfrm_import)
		self.lbl_constpath.configure(anchor="w", text="No File Selected")
		self.lbl_constpath.grid(column=1, row=2, sticky="ew")
		self.lbl_objpath = ttk.Label(self.lblfrm_import)
		self.lbl_objpath.configure(anchor="w", text="No File Selected")
		self.lbl_objpath.grid(column=1, row=1, sticky="ew")
		self.frame1 = ttk.Frame(self.lblfrm_import)
		self.radiobutton1 = ttk.Radiobutton(self.frame1)
		self.strvar_multipleobjs = tk.StringVar(value="single")
		self.radiobutton1.configure(
			text="Single Objective", value="single", variable=self.strvar_multipleobjs
		)
		self.radiobutton1.grid(column=0, padx=5, row=0, sticky="nsew")
		self.radiobutton1.configure(command=self.onradio_singleobj)
		self.radiobutton2 = ttk.Radiobutton(self.frame1)
		self.radiobutton2.configure(
			text="Many Objective Files", value="many", variable=self.strvar_multipleobjs
		)
		self.radiobutton2.grid(column=0, padx=5, row=1, sticky="nsew")
		self.radiobutton2.configure(command=self.onradio_manyobj)
		self.frame1.configure(height=200, padding=1, width=200)
		self.frame1.grid(column=0, columnspan=2, row=0)
		self.frame1.grid_anchor("center")
		self.frame1.rowconfigure(0, weight=1)
		self.frame1.columnconfigure(0, weight=1)
		self.frame1.columnconfigure(1, weight=1)
		self.lblfrm_import.configure(height=200, text="Import", width=500)
		self.lblfrm_import.grid(
			column=0, ipady=0, padx=0, pady=10, row=0, sticky="nsew"
		)
		self.lblfrm_import.rowconfigure(0, pad=10)
		self.lblfrm_import.rowconfigure(1, pad=10)
		self.lblfrm_import.columnconfigure(0, pad=5, weight=1)
		self.lblfrm_import.columnconfigure(1, pad=5, weight=5)
		self.lblfrm_run = ttk.Labelframe(self.frm_actualrunning)
		self.btn_run = ttk.Button(self.lblfrm_run)
		self.btn_run.configure(text="Run Model")
		self.btn_run.grid(
			column=0, columnspan=1, ipadx=10, ipady=5, padx=10, pady=10, row=1
		)
		self.btn_run.configure(command=self.onbtn_run_run)
		self.lbl_run_modelstats = ttk.Label(self.lblfrm_run)
		self.lbl_run_modelstats.configure(text="No Model Loaded")
		self.lbl_run_modelstats.grid(column=0, padx=10, pady=10, row=0, sticky="nsew")
		self.lblfrm_run.configure(height=200, text="Run", width=200)
		self.lblfrm_run.grid(column=0, pady=10, row=1, sticky="nsew")
		self.lblfrm_run.columnconfigure(0, weight=1)
		self.lblfrm_output = ttk.Labelframe(self.frm_actualrunning)
		self.btn_output = ttk.Button(self.lblfrm_output)
		self.btn_output.configure(text="Save Output")
		self.btn_output.grid(
			column=0, columnspan=1, ipadx=10, ipady=5, padx=10, pady=10, row=1
		)
		self.btn_output.configure(command=self.onbtn_output_save)
		self.lblfrm_output.configure(height=200, text="Output", width=200)
		self.lblfrm_output.grid(column=0, pady=10, row=2, sticky="nsew")
		self.lblfrm_output.columnconfigure(0, weight=1)
		self.frm_actualrunning.configure(height=200, width=1000)
		self.frm_actualrunning.grid(column=0, padx=0, pady=0, row=1, sticky="nsew")
		self.frm_actualrunning.rowconfigure(1, pad=10)
		self.frm_actualrunning.rowconfigure(2, pad=10)
		self.frm_actualrunning.columnconfigure(0, minsize=300, weight=1)
		self.lblfrm_status = ttk.Labelframe(self.im_a_top)
		self.txt_status = tk.Text(self.lblfrm_status)
		self.txt_status.configure(
			blockcursor="false", undo="true", width=70, wrap="word"
		)
		_text_ = text.SPLASH_STRING
		self.txt_status.insert("0.0", _text_)
		self.txt_status.grid(column=0, padx=10, pady=10, row=0, sticky="nsew")
		self.scroll_status = ttk.Scrollbar(self.lblfrm_status, command=self.txt_status.yview)
		self.scroll_status.configure(orient="vertical")
		self.scroll_status.grid(column=1, row=0, sticky="ns")
		self.txt_status['yscrollcommand'] = self.scroll_status.set
		self.lblfrm_status.configure(height=200, text="Status")
		self.lblfrm_status.grid(column=1, padx=20, pady=10, row=1, sticky="nsew")
		self.lblfrm_status.rowconfigure(0, weight=1)
		self.lblfrm_status.columnconfigure(0, weight=1)
		self.im_a_top.configure(height=200, padx=10, pady=10, width=200)
		self.im_a_top.rowconfigure(1, weight=1)
		self.im_a_top.columnconfigure(1, weight=1)
		self.im_a_top.columnconfigure(2, weight=1)

		# Main widget
		self.mainwindow = self.im_a_top

		self._init_styling()
		self._redraw_dynamics()

	def run(self):
		self.mainwindow.mainloop()


	def onradio_singleobj(self):
		# If we're switching the option, we want to reset everything
		if self.state.multipleObjFiles == True:
			self.state.objFileDirStr = ""
			self.state.objFileSingleStr = ""

			# Technically it doesn't make sense to reset the constraints
			# but it feels natural in the GUI
			self.state.constFileStr = ""

		self.state.multipleObjFiles = False

		self._redraw_dynamics()


	def onradio_manyobj(self):
		# If we're switching the option, we want to reset everything
		if self.state.multipleObjFiles == False:
			self.state.objFileDirStr = ""
			self.state.objFileSingleStr = ""
			self.state.constFileStr = ""

		self.state.multipleObjFiles = True

		self._redraw_dynamics()


	def onbtn_import_obj(self):
		'''
			Select objective csv or directory with a chooser
		'''
		if self.state.multipleObjFiles:
			# Load a directory
			inputObjDir = filedialog.askdirectory()

			if isInvalidDir(inputObjDir):
				self.state.objFileDirStr = ""
				self.state.objFileSingleStr = ""
			else:
				self.state.objFileDirStr = inputObjDir

		else:
			# Load a single file
			inputObjFile = filedialog.askopenfilename(
				filetypes=CSV_FILES,
				defaultextension=CSV_FILES
				)

			# TODO: Improve behaviour by checking if previous selection
			# is valid, so that selecting nothing doesn't clear everything
			if isInvalidFile(inputObjFile):
				self.state.objFileDirStr = ""
				self.state.objFileSingleStr = ""
			else:
				self.state.objFileSingleStr = inputObjFile
		
		self._redraw_dynamics()


	def onbtn_import_const(self):
		'''
			Select constraint file with csv chooser
		'''
		constrFileStr = filedialog.askopenfilename(
			filetypes=CSV_FILES,
			defaultextension=CSV_FILES
			)

		# TODO: Improve behaviour by checking if previous selection
		# is valid, so that selecting nothing doesn't clear everything
		if isInvalidFile(constrFileStr):
			self.state.constFileStr = ""
		else:
			self.state.constFileStr = constrFileStr
		
		self._redraw_dynamics()






	#
	# Loading / Linting the Model
	#

	def onbtn_import_load(self):
		'''
		This reads the objective and constraint files, linting them and
		reporting back any issues
		'''
		print("Loading model")
		status_str = ''

		if self.state.multipleObjFiles:
			status_str = self._load_dir_of_objective()
		else:
			status_str = self._load_single_obj()

		# reset any existing results
		self.state.runResults = None

		self._write_new_status(status_str)
		self._redraw_dynamics()


	def _load_dir_of_objective(self) -> str:
		'''
		Loads every .csv within the passed directory and returns a status string
		'''
		# Try loading every single file
		error_files = []
		warning_files = []
		perfect_files = []

		warnings_found: Set[str] = set()
		errors_found: Set[str] = set()

		self.state.objFilenames = []
		self.state.loadedModels = []

		for p in pathlib.Path(self.state.objFileDirStr).glob('*.csv'):
			objData, constrData, messages = converter.lintInputDataFromFilepaths(
				objFilePath=p,
				constrFilePath=self.state.constFileStr
			)

			if objData == None:
				# Error
				error_files.append(p.name)
				errors_found.update(messages)
			
			else:
				if len(messages) > 0:
					# Warnings
					warning_files.append(p.name)
					warnings_found.update(messages)
				else:
					# Perfect file
					perfect_files.append(p.name)
				
				self.state.objFilenames.append(p.name)

				self.state.loadedModels.append(
					converter.convertInputToFinalModel(
						objData=objData,
						constData=constrData
					)
				)

		
		# Now build the status string
		status_str = ""

		num_perfect = len(perfect_files)
		num_warning = len(warning_files)
		num_error = len(error_files)
		num_loaded = len(self.state.loadedModels)
		assert(num_loaded == num_perfect + num_warning)


		# Two ways to have an error
		if num_perfect + num_warning + num_error == 0:
			status_str += "[[ Error ]]\n"
			status_str += "No .csv files found in directory"
			status_str += self.state.objFileDirStr
			self.state.loadedModels = None
		
		elif num_loaded == 0:
			status_str += "[[ Error ]]\n"
			status_str += "All objective files loaded with errors."
			self.state.loadedModels = None
		
		else:
			status_str += "[[ Success ]]\n"
			status_str += "At least one objective file worked"

		status_str += "\n\n"


		# Give summary numbers
		status_str += f"Total Loaded: {num_loaded}\n" + \
					 f" - perfectly: {num_perfect}\n" + \
					 f" - with warning: {num_warning}\n" + \
					 f"Total Errored: {num_error}\n"

		# Report file names
		status_str += "\n\n === Files Loaded Perfectly ==="
		status_str += "\n ~ ".join([''] + perfect_files)

		status_str += "\n\n === Files Loaded with Warnings ==="
		status_str += "\n ! ".join([''] + warning_files)

		status_str += "\n\n === Files with Errors ==="
		status_str += "\n x ".join([''] + error_files)
		status_str += "\n\n\n\n"

		# Report erros and warnings
		if len(warnings_found) != 0:
			status_str += "\n!!!! Warnings found !!!!"
			status_str += "\n\n[[ Warning ]]\n".join([''] + list(warnings_found))

		if len(errors_found) != 0:
			status_str += "\n\n\nXXXX Errors found XXXX"
			status_str += "\n\n[[ Error ]]\n".join([''] + list(errors_found))

		return status_str


	def _load_single_obj(self) -> str:
		'''
		Loads the singular objective file and returns a status string
		'''
		objData, constrData, messages = converter.lintInputDataFromFilepaths(
			objFilePath=self.state.objFileSingleStr,
			constrFilePath=self.state.constFileStr
		)

		status_str = ""

		if objData == None:
			# Error
			status_str = "XXXXXX\n[[ Errors Occured - Unable to Convert ]]\n"
			status_str += "\n\n[[ Error ]]\n".join([''] + messages)
			self.state.loadedModels = None

		else:
			# Success
			status_str = "[[ Conversion Success ]]\n"
			if len(messages) >= 1:
				status_str += "\n\n[[ Warning ]]\n".join([''] + messages)
			self.state.loadedModels = [converter.convertInputToFinalModel(
				objData=objData, 
				constData=constrData
			)]
		
		return status_str





	def onbtn_run_run(self):
		print("Now do the run")

		self.state.runInstances = []
		self.state.runResults = []

		# Run all the models
		for lm in self.state.loadedModels:
			datadict = converter.convertFinalModelToDataDict(lm)
			instance = pyomo_runner.loadPyomoModelFromFinalModel(datadict)
			instance, res = pyomo_runner.solveConcreteModel(instance)

			self.state.runInstances.append(instance)
			self.state.runResults.append(res)

		# With a single run, output the results to the status
		if not self.state.multipleObjFiles:
			inst = self.state.runInstances[0]
			res = self.state.runResults[0]

			resStr = pyomo_runner.getOutputStr(inst, res)
			self._write_new_status(resStr)

		# Otherwise, create a summary
		else:
			# First sort successful runs (status 'ok') from non successful runs
			successful_runs = []
			successful_terminations = []

			failed_runs = []
			failed_terminations = []

			for ind, res in enumerate(self.state.runResults):
				status = res.solver.status
				termination = res.solver.termination_condition
				runfilename = self.state.objFilenames[ind]

				# List of possible status & term conditions
				# https://github.com/Pyomo/pyomo/blob/main/pyomo/opt/results/solver.py
				if status == 'ok':
					successful_runs.append(runfilename)
					successful_terminations.append(termination)
				else:
					failed_runs.append(runfilename)
					failed_terminations.append(termination)

			# Now build the status string
			statusStr = ""

			statusStr += " === OK Runs === \n"
			for name, term in zip(successful_runs, successful_terminations):
				statusStr += f"{name}: {term}\n"
			statusStr += "\n" * 3

			statusStr += " === Failed Runs === \n"
			for name, term in zip(failed_runs, failed_terminations):
				statusStr += f"{name}: {term}\n"

			self._write_new_status(statusStr)
		
		self._redraw_dynamics()



	def onbtn_output_save(self):
		'''
		Select a text file or directory to output to.
		'''
		msg = ''

		if self.state.multipleObjFiles:
			msg = self._do_multirun_output()
		else:
			msg = self._do_singlerun_output()

		self._write_new_status(msg)
		self._redraw_dynamics()


	def _do_singlerun_output(self) -> str:
		'''
		Asks the user for the valid info to output a single run,
		returns a status string.
		'''
		outputTxtFileStr = filedialog.asksaveasfilename(
			filetypes=TXT_FILES,
			defaultextension=TXT_FILES
		)

		if isInvalidFile(outputTxtFileStr):
			return "[[ XX Error ]]\nInvalid output file"
		
		print(self.state.runInstances)

		instance = self.state.runInstances[0]
		result = self.state.runResults[0]
		GuibuildingApp._output_single_run(outputTxtFileStr, instance, result)
		
		return f"[[ Success]]\n\nWrote to file {outputTxtFileStr}"


	def _do_multirun_output(self) -> str:
		'''
		Asks the user for a directory to output a whole batch of runs.
		'''
		outputDirectoryStr = filedialog.askdirectory()

		if isInvalidDir(outputDirectoryStr):
			return "[[ XX Error ]]\nInvalid output directory"
		outDir = pathlib.Path(outputDirectoryStr)
		
		# Within the directory, create a sub directory with the current time
		time_str = GuibuildingApp._get_timestamp()
		dirname = f'RunOutput-{time_str}'
		outDir = outDir.joinpath(dirname)

		try:
			os.mkdir(outDir)
		except Exception as excep:
			return f"[[ XX Error ]]\n{excep}"

		# For each run, output to directory
		PREFIX = 'rawPyoOut_'
		for ind, name in enumerate(self.state.objFilenames):
			name = name.split(".")[0]
			filename = PREFIX + name + '.txt'
			filepath = outDir.joinpath(filename)

			instance = self.state.runInstances[ind]
			result = self.state.runResults[ind]
			GuibuildingApp._output_single_run(filepath, instance, result)

		num_runs = len(self.state.runResults)
		return f"[[ Success ]]\n\nCreated directory {outDir} and wrote output for {num_runs} runs"


	@staticmethod
	def _output_single_run(outputFile: Union[str, pathlib.Path], 
							runInstance: pyo.ConcreteModel, 
							runResult: opt.SolverResults) -> None:
		'''
		Write a single run (successful or not) into to the directory
		'''
		runOut = pyomo_runner.getOutputStr(runInstance, runResult)
		with open(outputFile, 'w') as f:
			f.write(runOut)



	

	
	def _write_new_status(self, msg_str: str):
		'''
		Writes to the status box, clearing out whatever was there
		before and timestamping it.
		'''
		self.txt_status.delete("1.0", tk.END)

		# Insert Time Stamp
		time_str = GuibuildingApp._get_timestamp()
		self.txt_status.insert(tk.END, time_str + "\n\n")

		# Insert message
		self.txt_status.insert(tk.END, msg_str)


	@staticmethod
	def _get_timestamp():
		cur_time = time.localtime(time.time())
		time_str = "{Year}-{Month}-{Day}-{Hour}-{Min}-{Sec}".format(
			Year=cur_time.tm_year, 
			Month=str(cur_time.tm_mon).zfill(2),  # zfill pads the string with zeros
			Day=str(cur_time.tm_mday).zfill(2),   # i.e. "3" -> "03"
			Hour=str(cur_time.tm_hour).zfill(2),
			Min=str(cur_time.tm_min).zfill(2),
			Sec=str(cur_time.tm_sec).zfill(2)
		)

		return time_str


	def _init_styling(self):
		'''
		There's some style work that I don't know how to input into
		pyguru designer so instead it's done here
		'''
		# Buttons that are always green
		btns = [
			self.btn_constcsv,
			self.btn_objcsv
		]

		for b in btns:
			b['state'] = 'normal'
			b['style'] = 'Accent.TButton'
		
		# Text sizes
		self.lbl_title.configure(font=("Arial", 18))

		# Make the status box monospace
		self.txt_status.configure(font='TkFixedFont')




	def _redraw_dynamics(self):
		# Reset all dyanmics
		# buttons
		btns = [
			self.btn_output, 
			self.btn_loadmodel, 
			self.btn_run
		]

		for b in btns:
			b['state'] = 'disabled'
			b['style'] = ''

		# label
		self.lbl_run_modelstats.configure(text="No Model Loaded")

		# change the text on buttons
		if self.state.multipleObjFiles:
			self.btn_objcsv.config(text=text.BTNOBJ_DIR)
			self.btn_output.config(text=text.BTNSAVE_DIR)
			self.btn_run.config(text=text.BTNRUN_MANY)
		else:
			self.btn_objcsv.config(text=text.BTNOBJ_SINGLE)
			self.btn_output.config(text=text.BTNSAVE_SINGLE)
			self.btn_run.config(text=text.BTNRUN_SINGLE)



		# Stage 1: Files Selected for import
		if self.state.constFileStr == '':
			self.lbl_constpath.config(text=text.NO_FILE_SEL)
		else:
			self.lbl_constpath.config(text=shrinkPathString(self.state.constFileStr))

		fileLoc = self.state.objFileSingleStr
		dirLoc = self.state.objFileDirStr
		objLocStr = fileLoc if fileLoc != '' else dirLoc

		if objLocStr == '':
			self.lbl_objpath.config(text=text.NO_FILE_SEL)
		else:
			self.lbl_objpath.config(text=shrinkPathString(objLocStr))

		if self.state.constFileStr != '' and objLocStr != '':
			self.btn_loadmodel['state'] = 'normal'
			self.btn_loadmodel['style'] = 'Accent.TButton'
		
		else:
			# We reset all state for future steps
			self.state.loadedModels = None
			self.state.runResults = None
			return


		# Stage 2: Models loaded
		allLM = self.state.loadedModels

		if allLM != None:
			self.btn_run['state'] = 'normal'
			self.btn_run['style'] = 'Accent.TButton'

			sampleLM = allLM[0]

			num_vars = len(sampleLM.var_names)
			num_consts = len(sampleLM.eq_vec) + len(sampleLM.ge_vec) + len(sampleLM.le_vec)
			model_str = \
				f"Model Loaded\n" + \
				f"{num_vars} variables, {num_consts} constraints\n" + \
				f"EQ: {len(sampleLM.eq_vec)} | GE: {len(sampleLM.ge_vec)} | LE: {len(sampleLM.le_vec)}"
			
			if self.state.multipleObjFiles:
				model_str += '\n' + \
							f'Objectives Loaded: {len(allLM)}'

			self.lbl_run_modelstats.configure(text=model_str)
		
		else:
			self.state.runResults = None
			return
		

		# Stage 3: Models were run
		res = self.state.runResults

		if res == None:
			return

		# Even if it's a failed output, we can save it
		self.btn_output['state'] = 'normal'
		self.btn_output['style'] = 'Accent.TButton'











def isInvalidFile(dialogOutput) -> bool:
	# For whatever reason, filedialog.askname() can return multiple different things ???
	return dialogOutput == None or len(dialogOutput) == 0 or dialogOutput.strip() == ""


def isInvalidDir(dialogOutput) -> bool:
	return dialogOutput == None or type(dialogOutput) != str or dialogOutput.strip() == ""


def shrinkPathString(pathstr: str) -> str:
	pathstr = str(pathstr)
	if len(pathstr) <= PATH_DISPLAY_LEN:
		return pathstr
	else:
		return '...' + pathstr[3 - PATH_DISPLAY_LEN:]


def launchgui():
	print("Hello 👋")

	# Setup root
	root = tk.Tk()
	root.option_add("*tearOff", False)
	root.title("ForMOM - Linear Model Runner")

	# Load theme
	if ('.pyz' in __file__ or '.zip' in __file__):
		loadtheme_insidezip(root)
	else:
		loadtheme_unzipped(root)

	# Build the app and run
	app = GuibuildingApp(root)
	app.run()


def loadtheme_insidezip (root: tk.Tk):
	'''
	Loads the theme when the python file is inside a zip

	In the case of failure, no theme is used
	'''
	# When loading the theme, tcl needs to access an actual file
	# but when this program is built, it's inside a zip (.pyz).
	# So, we unzip the theme folder within the .pyz into a temp 
	# folder and send it to tcl,
	#
	# -\_(*_*)_/-
	style = ttk.Style(root)

	try:
		zip_dir = pathlib.Path(os.path.join(__file__, '..', '..')).resolve().absolute()

		with tempfile.TemporaryDirectory() as tmpdirname:
			# Extract into temp folder
			with zipfile.ZipFile(zip_dir, "r") as zip_ref:
				for file in zip_ref.namelist():
					if file.startswith('theme/'):
						zip_ref.extract(file, tmpdirname)
			
			# Feed it to tcl
			theme_path = os.path.join(tmpdirname, 'theme', 'forest-light.tcl')
			root.tk.call("source", theme_path)

		style.theme_use("forest-light")

	finally:
		return


def loadtheme_unzipped (root: tk.Tk):
	'''
	Loads the theme using relative paths 
	for when the application is not zipped
	'''
	style = ttk.Style(root)

	theme_path = pathlib.Path(os.path.join(
			__file__, 
			'..', 
			'..', 
			'theme', 
			'forest-light.tcl'))
	theme_path = theme_path.resolve().absolute()

	root.tk.call("source", str(theme_path))
	style.theme_use("forest-light")



if __name__ == "__main__":
	launchgui()




