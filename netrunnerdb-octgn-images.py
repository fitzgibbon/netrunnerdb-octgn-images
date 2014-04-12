import sys, os, argparse, re, pathlib, urllib.request, html.parser
import xml.etree.ElementTree as et
import unidecode

def download_netrunnerdb_images(octgn_path_map):
	p_cardname = re.compile(r"class=\"card-title\">(.+)<\/a>")
	for set_num in range(1, 10):
		for card_num in range(1, 200):
			page_url = "http://netrunnerdb.com/en/card/{:02d}{:03d}".format(set_num, card_num)
			#print(page_url)
			u = None
			try:
				for retry in range(10):
					if retry > 0:
						print("Retrying...")
					try:
						u = urllib.request.urlopen(page_url, timeout=10)
					except urllib.error.URLError:
						continue
					if u:
						break
			except urllib.request.HTTPError:
				if card_num == 1:
					return
				else:
					break
			hp = html.parser.HTMLParser()
			page = hp.unescape(u.read().decode("utf-8"))
			#print(page)
			m = p_cardname.search(page)
			if m and m.group(1):
				card_name = m.group(1)
				#print(card_name)
				ascii_card_name = unidecode.unidecode(card_name)
				#print(ascii_card_name)
				octgn_path = octgn_path_map.get(ascii_card_name.lower())
				if octgn_path:
					#print("-> " + octgn_path)
					img_url = "http://netrunnerdb.com/web/bundles/netrunnerdbcards/images/cards/en-large/{:02d}{:03d}.png".format(set_num, card_num)
					#print(img_url)
					print("{:s} ({:s} -> {:s})".format(card_name, img_url, octgn_path))
					for retry in range(10):
						if retry > 0:
							print("Retrying...")
						try:
							u = urllib.request.urlopen(img_url, timeout=10)
						except urllib.error.URLError:
							continue
						if u:
							break
					open(octgn_path, "wb").write(u.read())
				else:
					#print("-> *** No matching OCTGN path. ***")
					print("No OCTGN card path found for {:s} (ASCII conversion: {:s}, URL: {:s})".format(card_name, ascii_card_name, page_url), file=sys.stderr)
			else:
				if card_num == 1:
					return
				else:
					break

def get_octgn_path_map(game_path):
	path_map = {}
	set_paths = pathlib.Path(game_path).glob("Sets/*")
	for set_path in (str(x) for x in set_paths):
		set_root = et.parse(set_path + "/set.xml").getroot()
		set_name = set_root.attrib["name"]
		ignored_sets = set(["Markers", "Promos"])
		if set_name not in ignored_sets:
			for cards in set_root.iter("cards"):
				for card in cards.iter("card"):
					card_id = card.attrib["id"]
					card_name = card.attrib["name"]
					card_subtitle = None
					for prop in card.iter("property"):
						if prop.attrib["name"] == "Subtitle":
							card_subtitle = prop.attrib["value"]
					card_img_filename = set_path + "/Cards/" + card_id + ".png"
					card_full_name = card_name
					if card_subtitle:
						card_full_name += ": " + card_subtitle
					path_map[card_full_name.lower()] = card_img_filename
	return path_map

def main():
	"Download and install OCTGN Android: Netrunner card images from netrunnerdb.com."
	parser = argparse.ArgumentParser(description=main.__doc__)
	parser.add_argument("game_path", type=str, help="OCTGN Android:Netrunner game folder.")
	args = parser.parse_args()
	octgn_path_map = get_octgn_path_map(args.game_path)
	#print(octgn_path_map)
	download_netrunnerdb_images(octgn_path_map)

if __name__ == "__main__":
	main()