#!/usr/bin/env python3
import argparse
import datetime
import os
import shutil
import sys


CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
	sys.path.append(PARENT_DIR)

import lib.results as results


class ParsedTestRes:
	def __init__(self):
		self.result = "no_result"
		self.subclasses = []
		self.tabledata = {}


def parse_testres_file(file_path):
	parsed = ParsedTestRes()

	if not os.path.isfile(file_path):
		return parsed

	with open(file_path, "r") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue

			tokens = line.split(None)
			if not tokens:
				continue

			if tokens[0] == "TestResult" and len(tokens) >= 2:
				parsed.result = tokens[1]
			elif tokens[0] == "ResultSubClass" and len(tokens) >= 5:
				code = tokens[1]
				try:
					a = int(float(tokens[2]))
				except Exception:
					a = -1
				try:
					b = int(float(tokens[3]))
				except Exception:
					b = -1
				# Match ebuio.ResultFile behaviour: append trailing space after each token.
				# Hard-coded category keys in results.py (e.g. 'LARGER_MESH ') rely on this.
				message = ""
				for token in tokens[4:]:
					message += token + " "
				parsed.subclasses.append([code, a, b, message])
			elif tokens[0] == "tabledata" and len(tokens) >= 3:
				key = tokens[1]
				# Preserve the same trailing-space convention used by ebuio for tabledata values.
				value = ""
				for token in tokens[2:]:
					value += token + " "
				parsed.tabledata[key] = value

	return parsed


def list_testres_names(folder):
	names = set()
	for item in os.listdir(folder):
		if item.endswith(".testres"):
			names.add(item[:-8])
	return names


def _pick_subclass(parsed, idx):
	if idx < len(parsed.subclasses):
		return parsed.subclasses[idx]
	return None


def build_merged_result(result_1, result_2):
	"""Build merged testres content for folder1 vs folder2.

	Strategy: keep folder1's testres content verbatim, only replace each
	subclass's `b` (reference) value with folder2's corresponding `a`
	(its own output). This means:
	  - If folder1 was originally run with folder2 as reference, output
	    matches folder1 exactly.
	  - In general, TestResult and subclass messages remain folder1's
	    verdict; only the reference column is repointed.
	"""

	if result_1.subclasses or result_1.result != "no_result" or result_1.tabledata:
		base = result_1
		other = result_2
	else:
		base = result_2
		other = result_1

	merged_subclasses = []
	for idx, sub in enumerate(base.subclasses):
		code = sub[0]
		a_value = sub[1]
		message = sub[3]

		other_sub = _pick_subclass(other, idx)
		if other_sub is not None:
			b_value = other_sub[1]
		else:
			b_value = -1

		merged_subclasses.append([code, a_value, b_value, message])

	if not merged_subclasses:
		merged_subclasses.append(["1", -1, -1, "No result in either folder"])

	final_result = base.result if base.result else "no_result"

	merged_tabledata = dict(base.tabledata)

	return final_result, merged_subclasses, merged_tabledata


def write_testres_file(output_folder, job_name, final_result, subclasses, tabledata):
	"""Write a testres file in the same line format the simulator emits.

	Subclass messages and tabledata values are stored in-memory with a
	trailing space (matching ebuio.ResultFile). We strip the trailing
	space when writing so the on-disk file matches the simulator output.
	"""
	path = os.path.join(output_folder, job_name + ".testres")
	with open(path, "w") as f:
		f.write("TestResult %s\n" % final_result)
		f.write("NumSubClass %d\n" % len(subclasses))
		for code, a_value, b_value, message in subclasses:
			f.write(
				"ResultSubClass %s %d %d %s\n"
				% (str(code), int(a_value), int(b_value), str(message).rstrip())
			)
		for key, value in tabledata.items():
			f.write("tabledata %s %s\n" % (key, str(value).rstrip()))


def copy_debug_log_if_exists(source_folder, output_folder, job_name):
	src = os.path.join(source_folder, job_name + ".debug.runlog")
	dst = os.path.join(output_folder, job_name + ".debug.runlog")
	if os.path.isfile(src):
		shutil.copyfile(src, dst)


class _FakeSettings:
	pass


class _FakeOutput:
	def __init__(self):
		self.memMap = {}


class _FakeJobTable:
	def __init__(self, names):
		self.pathList = [[name, "DUMMYROOT"] for name in names]


def generate_html_report(output_folder, folder_2, job_names, note):
	settings = _FakeSettings()
	settings.output = output_folder
	settings.refoutput = folder_2
	settings.threads = 1
	settings.note = note
	settings.timeout = 0
	settings.prog = "folder-compare"
	settings.iroot = "DUMMYROOT"

	output_obj = _FakeOutput()
	pathlist = _FakeJobTable(job_names)

	results.Results(
		settings,
		output_obj,
		"0:00:00",
		0.0,
		1,
		note,
		pathlist,
	)


def make_default_output_folder(parent_folder):
	now = datetime.datetime.now().strftime("%Y_%m_%d(%H%M%S)")
	return os.path.join(parent_folder, "compare_" + now)


def ensure_folder(path):
	if not os.path.isdir(path):
		os.makedirs(path, exist_ok=True)


def parse_args():
	parser = argparse.ArgumentParser(
		description="Compare two existing suite result folders and generate a third comparison folder."
	)
	parser.add_argument("--folder1", required=True, help="Output folder used as new output (A).")
	parser.add_argument("--folder2", required=True, help="Output folder used as reference (B).")
	parser.add_argument("--out", default="", help="Generated folder path. If omitted, auto-create under folder1 parent.")
	parser.add_argument("--note", default="Generated by compare_result_folders.py", help="Note shown in HTML summary.")
	return parser.parse_args()


def main():
	args = parse_args()
	folder1 = os.path.normpath(args.folder1)
	folder2 = os.path.normpath(args.folder2)

	if not os.path.isdir(folder1):
		print("ERROR: folder1 does not exist: %s" % folder1)
		return 1

	if not os.path.isdir(folder2):
		print("ERROR: folder2 does not exist: %s" % folder2)
		return 1

	if args.out:
		out_folder = os.path.normpath(args.out)
	else:
		out_folder = make_default_output_folder(os.path.dirname(folder1))

	ensure_folder(out_folder)

	names_1 = list_testres_names(folder1)
	names_2 = list_testres_names(folder2)
	all_names = sorted(names_1.union(names_2))

	if not all_names:
		print("ERROR: No .testres files found in input folders.")
		return 1

	for name in all_names:
		file_1 = os.path.join(folder1, name + ".testres")
		file_2 = os.path.join(folder2, name + ".testres")

		parsed_1 = parse_testres_file(file_1)
		parsed_2 = parse_testres_file(file_2)

		final_result, subclasses, tabledata = build_merged_result(parsed_1, parsed_2)

		write_testres_file(out_folder, name, final_result, subclasses, tabledata)
		copy_debug_log_if_exists(folder1, out_folder, name)

	completed_file = os.path.join(out_folder, "completedjobs.txt")
	with open(completed_file, "w") as f:
		for name in all_names:
			f.write(name + " 0\n")

	generate_html_report(out_folder, folder2, all_names, args.note)

	print("Done")
	print("Folder1 (Output):   %s" % folder1)
	print("Folder2 (Reference): %s" % folder2)
	print("Generated Folder:   %s" % out_folder)
	print("Result HTML:        %s" % os.path.join(out_folder, "000results.html"))
	return 0


if __name__ == "__main__":
	sys.exit(main())
