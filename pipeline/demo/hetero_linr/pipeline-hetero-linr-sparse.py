from pipeline.backend.config import Backend
from pipeline.backend.config import WorkMode
from pipeline.backend.pipeline import PipeLine
from pipeline.component.dataio import DataIO
from pipeline.component.evaluation import Evaluation
from pipeline.component.hetero_linr import HeteroLinR
from pipeline.component.input import Input
from pipeline.component.intersection import Intersection
from pipeline.interface.data import Data

guest = 9999
host = 10000
arbiter = 10002

guest_train_data = {"name": "motor_hetero_guest", "namespace": "experiment"}
host_train_data = {"name": "motor_hetero_host", "namespace": "experiment"}

input_0 = Input(name="train_data")

pipeline = PipeLine().set_initiator(role='guest', party_id=guest).set_roles(guest=guest, host=host, arbiter=arbiter)
dataio_0 = DataIO(name="dataio_0", output_format="sparse", missing_fille=True, outlier_replace=False)

dataio_0.get_party_instance(role='guest', party_id=guest).algorithm_param(with_label=True,
                                                                          label_name="motor_speed",
                                                                          label_type="float")
dataio_0.get_party_instance(role='host', party_id=host).algorithm_param(with_label=False)

intersection_0 = Intersection(name="intersection_0")
hetero_linr_0 = HeteroLinR(name="hetero_linr_0", penalty="L2", optimizer="sgd", tol=0.001,
                           alpha=0.01, max_iter=2, early_stop="weight_diff", batch_size=100,
                           learning_rate=0.15, decay=0.0, decay_sqrt=False,
                           init_param={"init_method": "zeros"},
                           encrypted_mode_calculator_param={"mode": "fast"})

evaluation_0 = Evaluation(name="evaluation_0", eval_type="regression", pos_label=1)

pipeline.add_component(dataio_0, data=Data(data=input_0.data))
pipeline.add_component(intersection_0, data=Data(data=dataio_0.output.data))
pipeline.add_component(hetero_linr_0, data=Data(train_data=intersection_0.output.data))
pipeline.add_component(evaluation_0, data=Data(data=hetero_linr_0.output.data))

pipeline.compile()

pipeline.fit(backend=Backend.EGGROLL, work_mode=WorkMode.STANDALONE,
             feed_dict={input_0:
                           {"guest": {9999: guest_train_data},
                            "host": {10000: host_train_data}
                            }

                       })

print (pipeline.get_component("hetero_linr_0").get_model_param())
print (pipeline.get_component("hetero_linr_0").get_summary())
print (pipeline.get_component("evaluation_0").get_summary())



# predict

pipeline.predict(backend=Backend.EGGROLL, work_mode=WorkMode.STANDALONE,
                              feed_dict={input_0:
                                             {"guest":
                                                  {9999: guest_train_data},
                                              "host":
                                                  {10000: host_train_data}
                                              }
                                         })

with open("output.pkl", "wb") as fout:
    fout.write(pipeline.dump())
