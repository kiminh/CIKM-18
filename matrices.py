import csv
import math
import pickle
import argparse

import networkx as nx

from tqdm import tqdm
from argparse import RawTextHelpFormatter

from variables import *


DATA_FILE = 'data/train_non_clique.csv'


# Not author, paper or conference
def irrelevant(first_node, second_node):
	prefixes = ('f', 'top')
	return (first_node.startswith(prefixes) or second_node.startswith(prefixes))


def create_graphs():
	global A,P,C,Gp,Gc,Ap,Ac

	reader = csv.reader(open(DATA_FILE), delimiter='\t')

	# Author -> Papers 
	AP = {}

	# Paper -> Conferences 
	PC = {}

	print('Reading data file: ' + DATA_FILE + '...')

	for row in reader:
		node1, node2 = row[0], row[1]
		if irrelevant(node1, node2):
			continue
		
		if 	node2.startswith('a'):
			if node2 not in AP:
				AP[node2] = set()
			AP[node2].add(node1)

		elif node2.startswith('c'):
			if node1 not in PC:
				PC[node1] = set()
			PC[node1].add(node2)

		else:
			raise Exception('Received: ' + node1 + '_' + node2 + '\nSecond node must of type "author" or "conference"')

	# Author -> Conferences
	AC = {}
	max_papers, max_conf = -1,-1
	for author,papers in AP.items():
		AC[author] = set()
		for paper in papers:
			for conferences in PC[paper]:
				AC[author].add(conferences)
		# Compute maximum no. of papers and conferences by an author
		max_papers = max(max_papers, len(papers))
		max_conf   = max(max_conf, len(AC[author]))


	print('Maximum no. of papers/conferences for an author: ' + str(max_papers) + '/' + str(max_conf))

	A = [author for author,papers in AP.items()]
	P = [paper for paper,conferences in PC.items()]

	C_ = set()
	for paper,conference in PC.items():
		C_.add(list(conference)[0])
	
	C = list(C_)

	print('Generating author-paper and author-conference graphs...')

	# Initialise Graphs	
	Gp = nx.Graph()
	Gc = nx.Graph()

	Gp.add_nodes_from(A)
	Gp.add_nodes_from(P)

	for author,papers in AP.items():
		for paper in list(papers):
			Gp.add_edge(author,paper)
	
	Gc.add_nodes_from(A)
	Gc.add_nodes_from(C)

	for author,conferences in AC.items():
		for conference in list(conferences):
			Gc.add_edge(author,conference)


def DFSUtil(graph, visited, v, depth, limit, neighbors):
	visited[v] = True
	if depth == limit:
		neighbors[v] = 1
		return

	for u in graph.neighbors(v):
		if u in neighbors and depth == limit-1:
			neighbors[u] += 1
			continue
		if u not in visited:
			DFSUtil(graph, visited, u, depth+1, limit, neighbors)


def DFS(graph, source, limit=2):
	visited, neighbors = {}, {}
	DFSUtil(graph, visited, source, 0, limit, neighbors)
	return neighbors


def jaccard_coefficient(g, a, b, cn):
	deg_a = g.degree(a)
	deg_b = g.degree(b)
	return cn/(deg_a + deg_b - cn)


def adamic_adar(g, a, b):
	common_neighbors = [v for v in nx.common_neighbors(g, a, b)]
	return sum([1/math.log(g.degree(v)) for v in common_neighbors])


def resource_allocation(g, a, b):
	common_neighbors = [v for v in nx.common_neighbors(g, a, b)]
	return sum([1/g.degree(v) for v in common_neighbors])


def create_matrices(similarity, weighted):
	global Gp,Gc,Ap,Ac
	
	# Number of authors
	n_authors = len(A)

	# Initiliaze Ap,Ac
	Ap, Ac = {},{}

	print('Creating APA matrix..')
	for author in tqdm(A, ncols=100):
		Ap[author] = {}
		author_neighbours = DFS(graph=Gp, source=author, limit=2)
		
		# Common Neighbour
		if similarity == 'cn':
			for author_,w in author_neighbours.items():
				w_ = 1
				if weighted:
					w_ = w
				Ap[author][author_] = w_

		# Jaccard Coefficient
		elif similarity == 'jc':
			for author_,w in author_neighbours.items():
				w_ = 1
				if weighted:
					w_ = w
				Ap[author][author_] = jaccard_coefficient(Gp, author, author_, w_)

		# Adamic-Adar
		elif similarity == 'aa':
			for author_,w in author_neighbours.items():
				Ap[author][author_] = adamic_adar(Gp, author, author_)

		# Resource Allocation
		elif similarity == 'ra':
			for author_,w in author_neighbours.items():
				Ap[author][author_] = resource_allocation(Gp, author, author_)

		else:
			raise Exception('Invalid similarity measure: ', similarity)

	pickle.dump(Ap, open('matrices/apa_' + similarity + '_' + weighted + '.pkl','wb'))

	print('Creating ACA matrix..')
	for author in tqdm(A, ncols=100):
		Ac[author] = {}
		author_neighbours = DFS(graph=Gc, source=author, limit=2)
		
		# Common Neighbour
		if similarity == 'cn':
			for author_,w in author_neighbours.items():
				w_ = 1
				if weighted:
					w_ = w
				Ac[author][author_] = w_

		# Jaccard Coefficient
		elif similarity == 'jc':
			for author_,w in author_neighbours.items():
				w_ = 1
				if weighted:
					w_ = w
				Ac[author][author_] = jaccard_coefficient(Gc, author, author_, w_)

		# Adamic-Adar
		elif similarity == 'aa':
			for author_,w in author_neighbours.items():
				Ac[author][author_] = adamic_adar(Gc, author, author_)

		# Resource Allocation
		elif similarity == 'ra':
			for author_,w in author_neighbours.items():
				Ac[author][author_] = resource_allocation(Gc, author, author_)

		else:
			raise Exception('Invalid similarity measure: ', similarity)

	pickle.dump(Ap, open('matrices/aca_' + similarity + '_' + weighted + '.pkl','wb'))



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate APA and ACA matrices using given similarity measure.',
									 formatter_class=RawTextHelpFormatter)
	parser.add_argument('-s','--similarity', dest='similarity', default='cn',
			    help='Similarity measure between author nodes. Choose among following: \ncn - Common neighbour \njc - Jaccard Coefficient \naa - Adamic-Adar \nra - Resource Allocation. (default: cn)')
	parser.add_argument('-w','--weighted', dest='weighted', default=False,
			    help='Whether to have weighted similarity scores. (default: False)')
	
	args = parser.parse_args()

	# Create APA and ACA graphs
	create_graphs()

	# Create APA and ACA matrices
	create_matrices(similarity=args.similarity, weighted=bool(args.weighted))
