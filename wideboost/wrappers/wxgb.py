import numpy as np
import xgboost as xgb 
from ..objectives.squareloss import squareloss_gradient_hessian
from ..objectives.categoricallogloss import categoricallogloss_gradient_hessian
from ..objectives.binarylogloss import binarylogloss_gradient_hessian

def train(param,dtrain,num_boost_round=10,evals=(),obj=None,
          feval=None,maximize=False,early_stopping_rounds=None,evals_result=None,
          verbose_eval=True,xgb_model=None,callbacks=None):
    
    params = param.copy()
    assert params['extra_dims'] >= 0

    # Overwrite needed params
    print("Overwriting param `num_class`")
    try:
        nclass = params["num_class"]
    except:
        params['num_class'] = 1

    obj = get_objective(params)
    params['num_class'] = params['num_class'] + params['extra_dims']
    params.pop('extra_dims')

    print("Overwriting param `objective`")
    params['objective'] = 'reg:squarederror'

    try:
        params.pop('eval_metric')
        print("Removing param `eval_metric`.")
    except:
        None

    print("Setting param `disable_default_eval_metric` to 1.")
    params['disable_default_eval_metric'] = 1

    # TODO: base_score should be set depending on the objective chosen
    params['base_score'] = 0

    return obj, xgb.train(params,dtrain,num_boost_round=num_boost_round,evals=evals,obj=obj,
          feval=feval,maximize=maximize,early_stopping_rounds=early_stopping_rounds,
          evals_result=evals_result,verbose_eval=verbose_eval,xgb_model=xgb_model,
          callbacks=callbacks)


def get_objective(params):
    output_dict = {
        'binary:logistic':xgb_objective(params['extra_dims'],params['num_class'],binarylogloss_gradient_hessian),
        'reg:squarederror':xgb_objective(params['extra_dims'],params['num_class'],squareloss_gradient_hessian),
        'multi:softmax':xgb_objective(params['extra_dims'],params['num_class'],squareloss_gradient_hessian)
        }
    return output_dict[params['objective']]


class xgb_objective():
    def __init__(self,wide_dim,output_dim,obj):
        ## accepted values for obj are the functions
        ## associated with 
        ## "binary:logistic"
        ## "reg:squarederror"
        ## "multi:softmax"

        ## wide_dim is the number of additional dimensions
        ## beyond the output_dim. Can be 0.
        self.wide_dim = wide_dim
        self.output_dim = output_dim
        self.obj = obj

        #B = np.concatenate([np.eye(10),np.random.random([oodim,10])],axis=0)
        self.B = np.concatenate([np.eye(self.output_dim),
        np.random.random([self.wide_dim,self.output_dim])],axis=0)

    def __call__(self,preds,dtrain):
        Xhere = preds.reshape([preds.shape[0],-1])
        Yhere = dtrain.get_label()

        M = Xhere.shape[0]
        N = Xhere.shape[1]

        grad, hess = self.obj(Xhere,self.B,Yhere)

        grad = grad.reshape([M*N,1])
        hess = hess.reshape([M*N,1])

        return grad, hess
