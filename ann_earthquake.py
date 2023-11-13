# -*- coding: utf-8 -*-
"""ann_earthquake.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15fiv1uNjn-ma3U4HWWOhm4oFHvwtEvB0
"""

# Commented out IPython magic to ensure Python compatibility.
# %%capture
# import pandas as pd
# import numpy as np
# from matplotlib import pyplot as plt
# import torch
# from datetime import datetime
# import scipy as sp
# !pip install torchsummaryX
# from torchsummaryX import summary

trainData = pd.read_excel("trainData.xlsx")
testData = pd.read_excel("testData.xlsx")
valData = pd.read_excel("valData.xlsx")
print(trainData.head())

from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler(feature_range = (0, 1))

Xtrain = scaler.fit_transform(trainData.values.astype('float64')[:, :-1])
ytrain = trainData['R'].values.astype('float64')

Xval = scaler.transform(valData.values.astype('float64')[:, :-1])
yval = valData['R'].values.astype('float64')

Xtest = scaler.transform(testData.values.astype('float64')[:, :-1])
ytest = testData['R'].values.astype('float64')

class FullyConnected(torch.nn.Module):
  def __init__(self, input_size, hidden_size, output_size, device):
    super(FullyConnected, self).__init__()
    self.D = input_size
    self.M = hidden_size
    self.K = output_size
    self.h = torch.nn.Linear(self.D, self.M, device = device)
    self.y = torch.nn.Linear(self.M, self.K, device = device)
    self.device = device
  def forward(self, X):
    out = self.h(X)
    out = torch.nn.functional.relu(out)
    out = torch.nn.functional.dropout(out, p = 0.1)
    out = self.y(out)
    out = torch.nn.functional.relu(out)
    return  out

def training_loop(hidden_size, Xtrain, ytrain, Xtest, ytest, Xval, yval, id):
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  print(device)
  model = FullyConnected(input_size = 7,
                        hidden_size = hidden_size,
                        output_size = 1,
                        device = device)
  summary(model, torch.zeros((1, 7), device = device))

  optimizer = torch.optim.Adam(model.parameters())
  criterion = torch.nn.MSELoss()

  n_epochs = 1001
  train_losses = []
  val_losses = []
  #training loop
  for it in range(n_epochs):
    t0 = datetime.now()
    optimizer.zero_grad()
    rndperm = np.random.permutation(range(Xtrain.shape[0]))
    inputs = torch.Tensor(Xtrain[rndperm, :]).to(device)
    target = torch.Tensor(ytrain[rndperm]).to(device).view(-1, 1)
    pred = model(inputs)
    loss = criterion(pred, target)
    loss.backward()
    optimizer.step()
    train_losses.append(loss.item())

    # validation
    with torch.no_grad():
      rndperm = np.random.permutation(range(Xval.shape[0]))
      inputs = torch.Tensor(Xval[rndperm, :]).to(device)
      target = torch.Tensor(yval[rndperm]).to(device).view(-1, 1)
      pred = model(inputs)
      loss = criterion(pred, target)
      val_losses.append(loss.item())

    if it % 100 == 0:
      t1 = datetime.now()
      print(f'Epoch: {it} Train Loss: {train_losses[it]:.3f} \
              Validation Loss: {val_losses[it]:.3f} Elapsed: {t1 - t0}s')

  with torch.no_grad():
    inputs = torch.Tensor(Xtest).to(device)
    target = torch.Tensor(ytest).to(device).view(-1, 1)
    pred = model(inputs)
    loss = criterion(pred, target)
    print(f'Test Loss: {loss.item():.3f}')
    pred = pred.cpu().view(-1).numpy()
    target = target.view(-1).cpu().numpy()
    r, p = sp.stats.pearsonr(pred, target)
    p = f'p = {p:.3f}' if p >= 0.005 else 'p < 0.005'
    print(f'R = {r:.3f}, {p}')
    plt.scatter(target, pred, c='black', marker='.', s=100)
    plt.plot([target.min(), target.max()], [pred.min(), pred.max()], color = 'red', linewidth = 2)
    plt.title(f'R = {r:.3f} and {p} for h = {hidden_size}')
    plt.xlabel('True Value')
    plt.ylabel('Prediction Value')
    plt.savefig(f'Model{hidden_size}Correlation{id}.png', dpi = 300, format = 'png')
    plt.show()

  plt.plot(range(n_epochs), train_losses, color = 'black', linewidth = 2)
  plt.plot(range(n_epochs), val_losses, color = 'gray', linewidth = 2, linestyle = 'dashed', alpha = 0.8)
  plt.xlabel('Epochs')
  plt.ylabel('MSE Loss')
  plt.title(f'Training and Validation Learning Curve for h = {hidden_size}')
  plt.savefig(f'Model{hidden_size}Learning{id}.png', dpi = 300, format = 'png')
  plt.show()
  return model, loss.item()

losses = []
models = []
for h in [10, 20, 30, 40, 50, 60]:
  loss_bundle = []
  model_bundle = []
  for id in range(5):
    model, loss = training_loop(hidden_size=h,
                                Xtrain = Xtrain,
                                ytrain = ytrain,
                                Xtest = Xtest,
                                ytest = ytest,
                                Xval = Xval,
                                yval = yval,
                                id = id + 1)
    model_bundle.append(model)
    loss_bundle.append(loss)

  losses.append(np.mean(loss_bundle))
  best = np.argmin(loss_bundle)
  models.append(model_bundle[best])

best_of_the_best = np.argmin(losses)
bestModel = models[best_of_the_best]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print('Best Model Summary')
summary(bestModel, torch.zeros((1,7), device = device))
print(f'Best model was h = {bestModel.M} with loss = {losses[best_of_the_best]:.3f}')
torch.save(bestModel.state_dict(), 'best_model.pt')

!zip -r /content/all_files.zip /content