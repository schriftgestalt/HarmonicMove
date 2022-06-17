# encoding: utf-8

###########################################################################################################
#
#
#	Select Tool Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/SelectTool
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
from math import sqrt
from scipy.optimize import fsolve
from GlyphsApp import *
from GlyphsApp.plugins import *

def getIntersection( x1,y1, x2,y2, x3,y3, x4,y4 ):
	px = ( (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4) ) / ( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) ) 
	py = ( (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4) ) / ( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) )
	return px, py

def derivative(p0,p1,p2,p3,t):
	return 3*((1-t)**2)*(p1-p0) +6*(1-t)*t*(p2-p1) + 3*(t**2)*(p3-p2)

def second_derivative(p0,p1,p2,p3,t):
	return 6*(1-t)*(p2-2*p1+p0)+6*t*(p3-2*p2+p1)

def curvature(x0,y0,x1,y1,x2,y2,x3,y3, t):
	dx = derivative(x0, x1, x2, x3, t)
	ddx = second_derivative(x0, x1, x2, x3, t)
	dy = derivative(y0, y1, y2, y3, t)
	ddy = second_derivative(y0, y1, y2, y3, t)
	return (ddx * dy - ddy * dx) / ((dy ** 2 + dx ** 2) ** 1.5)

		

def get_line_params(x0,y0,x1,y1):
	if x0-x1 != 0:
		z = (y0-y1)/(x0-x1)
	else :
		z = 0
	b = (y0+y1 - z*(x0+x1))/2
	return z, b


#todos
# fsolve → ?
# only scale handles?
# move anyway if cant

def find_selected_node(layer):
	if len(layer.selection) != 1:
			return
	for shape in layer.shapes:
		if not shape.nodes:
			continue
		for node in shape.nodes:
			if node in layer.selection:
				return (node, node.nextNode, node.nextNode.nextNode, node.prevNode, node.prevNode.prevNode)

def is_p1(node, N, P):
	return  node.type == 'offcurve' and N.type =='offcurve'

def is_p2(node, N, P):
	return node.type == 'offcurve' and P.type =='offcurve'


class ____PluginClassName____(SelectTool):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({'en': u'My Select Tool', 'de': u'Mein Auswahlwerkzeug'})
		self.generalContextMenus = [
			{'name': Glyphs.localize({'en': u'Layer info in Macro window', 'de': u'Ebenen-Infos in Makro-Fenster'}), 'action': self.printInfo_},
		]
		self.keyboardShortcut = 'c'

	@objc.python_method
	def start(self):
		pass
	
	@objc.python_method
	def activate(self):
		pass
	
	@objc.python_method
	def background(self, layer):
		if len(layer.selection) != 1:
			return
		node, N, NN, P, PP = find_selected_node(layer)
		
		if is_p1(node, N, P) :
			xIntersect, yIntersect = (
							getIntersection( 
								node.x, node.y, P.x, P.y,
								N.x, N.y, NN.x, NN.y,
								) 
							)
			intersection = NSPoint( xIntersect, yIntersect )
		
		if is_p2(node, N, P): 
			xIntersect, yIntersect = (
							getIntersection( 
								node.x, node.y, N.x, N.y,
								P.x, P.y, PP.x, PP.y,
								) 
							)
			intersection = NSPoint( xIntersect, yIntersect )
		
		if intersection:
			handleSize = 5
			rect = NSRect()
			rect.origin = NSPoint(intersection.x-handleSize/2, intersection.y-handleSize/2)
			rect.size = NSSize(handleSize, handleSize)
			NSBezierPath.bezierPathWithOvalInRect_(rect).fill()

					

	@objc.python_method
	def deactivate(self):
		pass
	

	def moveSelectionWithPoint_withModifier_(self, delta,modidierKeys):
		print(delta, modidierKeys, self.draggStart(), self.dragging())
		draggStart = self.draggStart()
		isDragging = self.dragging()
		
		layer = self.editViewController().graphicView().activeLayer()
		if len(layer.selection) != 1:
			return
		node, N, NN, P, PP = find_selected_node(layer)



		#target_positon = addPoints(draggStart, delta) if isDragging else addPoints(node.position, delta)
			
		if is_p1(node, N, P):
			print ('P1')
			x0, y0, x1,y1, x2,y2,x3,y3 = P.x, P.y, node.x, node.y, N.x, N.y, NN.x, NN.y
			
			# z0, b0 = get_line_params(x0,y0,x1,y1)
			# target_x = draggStart.x + delta[0] if isDragging else node.position.x + delta[0]
			# target_y = z0*target_x+b0
			# target_positon = NSPoint(target_x, target_y)

			
			initial_k = curvature(x0,y0, x1,y1, x2,y2,x3,y3,0)


			if (x2 == x3):
				def to_solve(to_optimize):
					return initial_k -curvature(x0,y0,target_positon.x,target_positon.y,x2,to_optimize,x3,y3,0)
				
				new_y2 = fsolve(to_solve, N.y)[0]		

				N.position = NSPoint(x2, new_y2)
				node.position = target_positon
			else:
				z, b = get_line_params(x2,y2,x3,y3)

				def to_solve(new_x2):
					new_y2 = z*new_x2+b
					return initial_k -curvature(x0,y0,target_positon.x,target_positon.y,new_x2,new_y2,x3,y3,0)
				new_x2 = fsolve(to_solve, x2)[0]
				print('solution', to_solve(new_x2), new_x2)
				
				N.position = NSPoint(new_x2, z*new_x2+b)
				node.position = target_positon

		elif is_p2(node, N, P):
			print ('P2' )
			target_positon = addPoints(draggStart, delta) if isDragging else addPoints(node.position, delta)
	
			x0, y0, x1,y1, x2,y2,x3,y3 = PP.x, PP.y, P.x, P.y, node.x, node.y, N.x, N.y
			initial_k = curvature(x0, y0, x1,y1, x2,y2,x3,y3, 1)

		
			if (x0 == x1):
				def to_solve(new_y1):
					return initial_k -curvature(x0,y0,x1, new_y1,target_positon.x,target_positon.y,x3,y3,1)

				new_y1 = fsolve(to_solve, y1)[0]
				P.position = NSPoint(x1, new_y1)
				node.position = target_positon
			else:
				z, b = get_line_params(x0,y0,x1,y1)
				def to_solve(new_x1):
					new_y1 = z*new_x1+b
					return initial_k -curvature(x0,y0,new_x1,new_y1,target_positon.x,target_positon.y, x3,y3,1)

				new_x1 = fsolve(to_solve, x1)[0]
				P.position = NSPoint(new_x1, z*new_x1+b)
				node.position = target_positon
		else:
			objc.super(____PluginClassName____, self).moveSelectionWithPoint_withModifier_(delta, modidierKeys)


	def printInfo_(self, sender):

		# Execute only if layers are actually selected
		if Glyphs.font.selectedLayers:
			layer = Glyphs.font.selectedLayers[0]
		
			# Do stuff:
			print("Current layer:", layer.parent.name, layer.name)

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
