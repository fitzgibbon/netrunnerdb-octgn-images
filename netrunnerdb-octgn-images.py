import sys, os, argparse, re, pathlib, urllib.request, html.parser
import xml.etree.ElementTree as et
import unidecode

def get_url(url):
	content = None
	try:
		for retry in range(3):
			if retry > 0:
				print("Retrying...")
			try:
				u = urllib.request.urlopen(url, timeout=30)
			except urllib.error.URLError:
				continue
			try:
				content = u.read()
			except:
				continue
			break
	except urllib.request.HTTPError:
		return None
	return content

def download_netrunnerdb_images(octgn_path_map):
	p_cardname = re.compile(r"class=\"card-title\">(.+)<\/a>")
	for set_num in range(1, 10):
		for card_num in range(1, 200):
			page_url = "http://netrunnerdb.com/en/card/{:02d}{:03d}".format(set_num, card_num)
			#print(page_url)
			cache_path_page = "cache/{:02d}{:03d}".format(set_num, card_num)
			content = None
			if os.path.exists(cache_path_page):
				content = open(cache_path_page, "rb").read()
			else:
				content = get_url(page_url)
				if content:
					if not os.path.exists("cache"):
						os.makedirs("cache")
					open(cache_path_page, "wb").write(content)
			if not content:
				if card_num == 1:
					return
				else:
					break
			hp = html.parser.HTMLParser()
			page = hp.unescape(content.decode("utf-8"))
			#print(page)
			m = p_cardname.search(page)
			if m and m.group(1):
				card_name = m.group(1)
				#print(card_name)
				ascii_card_name = unidecode.unidecode(card_name)
				#print(ascii_card_name)
				card_name_fixups = {
					"Melange Mining Corp." : "Melange Mining Corp",
					"NBN: The World is Yours*" : "NBN: The World is Yours"
				}
				fixed = card_name_fixups.get(ascii_card_name)
				if fixed:
					ascii_card_name = fixed
				octgn_path = octgn_path_map.get(ascii_card_name.lower())
				if octgn_path:
					#print("-> " + octgn_path)
					img_url = "http://netrunnerdb.com/web/bundles/netrunnerdbcards/images/cards/en-large/{:02d}{:03d}.png".format(set_num, card_num)
					#print(img_url)
					print("{:s} ({:s} -> {:s})".format(ascii_card_name, img_url, octgn_path))
					cache_path_img = "cache/{:02d}{:03d}.png".format(set_num, card_num)
					content = None
					if os.path.exists(cache_path_img):
						content = open(cache_path_img, "rb").read()
					else:
						content = get_url(img_url)
						if content:
							if not os.path.exists("cache"):
								os.makedirs("cache")
							open(cache_path_img, "wb").write(content)
					if content:
						open(octgn_path, "wb").write(content)
				else:
					#print("-> *** No matching OCTGN path. ***")
					print("No OCTGN card path found for ASCII conversion: {:s}, URL: {:s}".format(ascii_card_name, page_url), file=sys.stderr)
					print("Original card name: {:s}".format(card_name))
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