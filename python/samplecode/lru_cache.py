class DLLNode:
    def __init__(self, key, val):
        self.key = key
        self.val = val 
        self.prev = None
        self.next = None
    
class LRUCache(object):

    def __init__(self, capacity):
        """
        :type capacity: int
        """
        self.cap = capacity
        self.m = {}
        self.head = DLLNode(-1, -1)
        self.tail = DLLNode(-1, -1)
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def add_to_tail(self, node):
        prev = self.tail.prev

        node.prev = prev
        node.next = self.tail

        self.tail.prev = node
        prev.next = node
    
    def delete(self, node):

        prev_node = node.prev
        next_node = node.next

        prev_node.next = next_node
        next_node.prev = prev_node
    
    def move_to_tail(self, node):

        self.delete(node)

        self.add_to_tail(node)
        

    def get_node_after_head(self):

        if self.head.next == self.tail:
            return None
        
        return self.head.next
        

    def get(self, key):
        """
        :type key: int
        :rtype: int
        """
        if key in self.m:
            node = self.m[key]
            self.move_to_tail(node)
            return self.m[key].val
        return -1        

    def put(self, key, value):
        """
        :type key: int
        :type value: int
        :rtype: None
        """
        if key in self.m:
            node = self.m[key]
            node.val = value
            self.move_to_tail(node)
            return 
        
        node = DLLNode(key, value)

        if len(self.m) == self.cap:
            vacate = self.get_node_after_head()
            if vacate:
                self.delete(vacate)
                del self.m[vacate.key]
            else:
                return
        
        self.m[key] = node
        self.add_to_tail(node)

