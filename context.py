import math
import pickle
import argparse

from tqdm import tqdm
from argparse import RawTextHelpFormatter

SCALE = 100

# Generate contexts from ACA and/or APA matrices
def generate_contexts(combine, similarity, weighted, alpha):
	Ap = pickle.load(open('matrices/apa_' + similarity + '_' + weighted + '.pkl','rb'))
	Ac = pickle.load(open('matrices/aca_' + similarity + '_' + weighted + '.pkl','rb'))

	# String to hold the entire context
	contexts = ''

	# List of authors
	A = [author for author, author_neighbours in Ac.items()]
	
	print('Generating context...')
	for author in tqdm(A, ncols=100):
		context = ''

		if combine == 'aca':
			author_neighbours = Ac[author]
			
			if similarity == 'cn':
				for author_, w in author_neighbours.items():
					if w > 0:
						context += (author + ' ' + author_ + ' ') * w

			elif similarity in ['jc', 'aa', 'ra']:
				for author_, w in author_neighbours.items():
					w_= math.ceil(w * SCALE)
					if w_ > 0:
						context += (author + ' ' + author_ + ' ') * w_
			else:
				raise Exception('Invalid similarity measure: ', similarity)

		elif combine == 'apa':
			author_neighbours = Ap[author]

			if similarity == 'cn':
				for author_, w in author_neighbours.items():
					if w > 0:
						context += (author + ' ' + author_ + ' ') * w

			elif similarity in ['jc', 'aa', 'ra']:
				for author_, w in author_neighbours.items():
					w_= math.ceil(w * SCALE)
					if w_ > 0:
						context += (author + ' ' + author_ + ' ') * w_
			else:
				raise Exception('Invalid similarity measure: ', similarity)
		
		elif combine == 'sum':		
			author_neighbours_c = Ac[author]
			author_neighbours_p = Ap[author]

			if similarity == 'cn':
				for author_, w in author_neighbours_c.items():
					w_ = w
					if author_ in author_neighbours_p:
						w_ += author_neighbours_p[author_]
					if w_ > 0:
						context += (author + ' ' + author_ + ' ') * w_

			elif similarity in ['jc', 'aa', 'ra']:
				for author_, w in author_neighbours_c.items():
					w_ = w
					if author_ in author_neighbours_p:
						w_ += author_neighbours_p[author_]
					w_= math.ceil(w * SCALE)
					if w_ > 0:
						context += (author + ' ' + author_ + ' ') * w_
			else:
				raise Exception('Invalid similarity measure: ', similarity)
		
		elif combine == 'alpha':		
			author_neighbours_c = Ac[author]
			author_neighbours_p = Ap[author]

			if similarity == 'cn':
				for author_, w in author_neighbours_c.items():
					w_ = alpha * w
					if author_ in author_neighbours_p:
						w_ += (1 - alpha) * author_neighbours_p[author_]
					w_= math.ceil(w * SCALE)
					if w_ > 0:
						context += (author + ' ' + author_ + ' ') * w_

			elif similarity in ['jc', 'aa', 'ra']:
				for author_, w in author_neighbours_c.items():
					w_ = alpha * w
					if author_ in author_neighbours_p:
						w_ += (1 - alpha) * author_neighbours_p[author_]
					w_= math.ceil(w * SCALE)
					if w_ > 0:
						context += (author + ' ' + author_ + ' ') * w_
			else:
				raise Exception('Invalid similarity measure: ', similarity)

		else:
			raise Exception('Invalid combination rule: ', combine)

		contexts += context + '\n'

	if combine == 'alpha':
		context_file = open('contexts/context_' + combine + '_' + similarity + '_' + str(weighted) + '_' + str(alpha) + '.txt','w')
	else:
		context_file = open('contexts/context_' + combine + '_' + similarity + '_' + str(weighted) + '.txt','w')

	print('Saving to ', context_file.name)
	context_file.write(contexts)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Generate contexts from ACA and/or APA matrices.',
									 formatter_class=RawTextHelpFormatter)
	parser.add_argument('-c','--combine', dest='combine', default='aca',
			    help='Combination of similarity scores from APA and ACA matrices. Choose among aca,apa,sum,alpha. (default: aca)')
	parser.add_argument('-s','--similarity', dest='similarity', default='cn',
			    help='Similarity measure between author nodes. Choose among cn,jc,aa,ra. (default: cn)')
	parser.add_argument('-w','--weighted', dest='weighted', default=False,
			    help='Whether to have weighted similarity scores. (default: False)')
	parser.add_argument('-a','--alpha', dest='alpha', default='0.5',
			    help='Alpha value used in conjunction with alpha combination rule. \nsimilarity = alpha * ACA + (1 - alpha) * APA \nValue between 0 and 1. (default: 0.5)')

	args = parser.parse_args()

	# Generate contexts
	generate_contexts(combine=args.combine, similarity=args.similarity, weighted=args.weighted, alpha=float(args.alpha))
