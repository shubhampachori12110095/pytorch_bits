import math
import torch
from torch.autograd import Variable
from torch.nn.parameter import Parameter
import torch.nn.functional as F

from .rnn_cell_base import RNNCellBase

class MGU(RNNCellBase):

    def __init__(self, input_size, hidden_size, bias=True, sigmoid=None, tanh=None):
        super(MGU, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.bias = bias
        self.sigmoid = F.sigmoid if sigmoid is None else self.get_activation(sigmoid)
        self.tanh = F.tanh if tanh is None else self.get_activation(tanh)
        self.weight_ih = Parameter(torch.Tensor(2 * hidden_size, input_size))
        self.weight_hh = Parameter(torch.Tensor(2 * hidden_size, hidden_size))
        if bias:
            self.bias_ih = Parameter(torch.Tensor(2 * hidden_size))
            self.bias_hh = Parameter(torch.Tensor(2 * hidden_size))
        else:
            self.register_parameter('bias_ih', None)
            self.register_parameter('bias_hh', None)
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1.0 / math.sqrt(self.hidden_size)
        for weight in self.parameters():
            weight.data.uniform_(-stdv, stdv)
        self.hidden = None
    
    def reset_hidden(self):
        self.hidden = None
        self.timesteps = 0
        self.weight_ih.detach_()
        self.weight_hh.detach_()
        if self.bias: 
            self.bias_ih.detach_()
            self.bias_hh.detach_()
    
    def detach_hidden(self):
        self.hidden.detach_()
        self.weight_ih.detach_()
        self.weight_hh.detach_()
        if self.bias: 
            self.bias_ih.detach_()
            self.bias_hh.detach_()

    def forward(self, input_data, future=0):
        timesteps, batch_size, features = input_data.size()
        # print("t %d, b %d, f %d" % (timesteps, batch_size, features))
        outputs = Variable(torch.zeros(timesteps + future, batch_size, self.hidden_size), requires_grad=False)
        
        if self.hidden is None:
            self.hidden = Variable(torch.zeros(batch_size, self.hidden_size), requires_grad=False)
        
        self.check_forward_input(input_data[0])
        self.check_forward_hidden(input_data[0], self.hidden)
        
        for i, input_t in enumerate(input_data.split(1)):
            
            gi = F.linear(input_t.view(batch_size, features), self.weight_ih, self.bias_ih)
            gh = F.linear(self.hidden, self.weight_hh, self.bias_hh)
            i_f, i_n = gi.chunk(2, 1)
            h_f, h_n = gh.chunk(2, 1)

            forgetgate = self.sigmoid(i_f + h_f)
            newgate = self.tanh(i_n + forgetgate * h_n)
            self.hidden = newgate + (1 - forgetgate) * (self.hidden - newgate)
            outputs[i] = self.hidden
        
        return outputs

class MGU2(RNNCellBase):

    def __init__(self, input_size, hidden_size, bias=True, sigmoid=None, tanh=None):
        super(MGU2, self).__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.bias = bias
        self.sigmoid = F.sigmoid if sigmoid is None else self.get_activation(sigmoid)
        self.tanh = F.tanh if tanh is None else self.get_activation(tanh)
        self.weight_ih = Parameter(torch.Tensor(hidden_size, input_size))
        self.weight_hh = Parameter(torch.Tensor(2 * hidden_size, hidden_size))
        if bias:
            self.bias_ih = Parameter(torch.Tensor(hidden_size))
            self.bias_hh = Parameter(torch.Tensor(2 * hidden_size))
        else:
            self.register_parameter('bias_ih', None)
            self.register_parameter('bias_hh', None)
        self.reset_parameters()

    def reset_parameters(self):
        stdv = 1.0 / math.sqrt(self.hidden_size)
        for weight in self.parameters():
            weight.data.uniform_(-stdv, stdv)
        self.hidden = None
    
    def reset_hidden(self):
        self.hidden = None
        self.timesteps = 0
        self.weight_ih.detach_()
        self.weight_hh.detach_()
        if self.bias: 
            self.bias_ih.detach_()
            self.bias_hh.detach_()
    
    def detach_hidden(self):
        self.hidden.detach_()
        self.weight_ih.detach_()
        self.weight_hh.detach_()
        if self.bias: 
            self.bias_ih.detach_()
            self.bias_hh.detach_()

    def forward(self, input_data, future=0):
        timesteps, batch_size, features = input_data.size()
        # print("t %d, b %d, f %d" % (timesteps, batch_size, features))
        outputs = Variable(torch.zeros(timesteps + future, batch_size, self.hidden_size), requires_grad=False)
        
        if self.hidden is None:
            self.hidden = Variable(torch.zeros(batch_size, self.hidden_size), requires_grad=False)
        
        self.check_forward_input(input_data[0])
        self.check_forward_hidden(input_data[0], self.hidden)
        
        for i, input_t in enumerate(input_data.split(1)):
            
            i_n = F.linear(input_t.view(batch_size, features), self.weight_ih, self.bias_ih)
            gh = F.linear(self.hidden, self.weight_hh, self.bias_hh)
            h_f, h_n = gh.chunk(2, 1)

            forgetgate = self.sigmoid(h_f)
            newgate = self.tanh(i_n + forgetgate * h_n)
            self.hidden = newgate + (1 - forgetgate) * (self.hidden - newgate)
            outputs[i] = self.hidden
        
        return outputs
