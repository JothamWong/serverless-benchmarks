# Chaining

There are two implementation strategies when it comes to chaining separate serverless functions, as opposed to just calling function b from function a's code itself.

We have inline transfer, wherein the serverless framework passes the result of function a to function b directly.
The alternative is the use of an external storage such as an S3 bucket or minio instance, where function a uploads its results to the bucket instance, function b is invoked and retrieves its arguments from the bucket. This comes with serialization and deserialization, plus networking penalties.

At the moment, SeBS does not have support for studying of function chaining. We will implement inline transfer using Openwhisk Sequences.

## Openwhisk Sequences

In one window, run

```bash
wsk -i activation poll
```

In another, run

```bash
$ wsk action create mySequence --sequence /whisk.system/utils/split,/whisk.system/utils/sort
ok: created action mySequence
$ wsk action invoke --result mySequence --param payload "Over-ripe sushi,\nThe Master\nIs full of regret."
{
    "length": 3,
    "lines": [
        "Is full of regret.",
        "Over-ripe sushi,",
        "The Master"
    ]
}
```

In the activation poll, the following is observed:

```bash
Activation: 'sort' (f73e7859ceb2428dbe7859ceb2328db1)
[
    "2024-06-14T19:19:17.789601201Z stdout: sort input msg: {\"lines\":[\"Over-ripe sushi,\",\"The Master\",\"Is full of regret.\"],\"payload\":\"Over-ripe sushi,\\nThe Master\\nIs full of regret.\"}",
    "2024-06-14T19:19:17.789683705Z stdout: sort before: Over-ripe sushi,,The Master,Is full of regret.",
    "2024-06-14T19:19:17.789774816Z stdout: sort after: Is full of regret.,Over-ripe sushi,,The Master"
]

Activation: 'split' (78895e1d1af84fcd895e1d1af86fcdf2)
[
    "2024-06-14T19:19:17.769820472Z stdout: split: returning {\"lines\":[\"Over-ripe sushi,\",\"The Master\",\"Is full of regret.\"],\"payload\":\"Over-ripe sushi,\\nThe Master\\nIs full of regret.\"}"
]

Activation: 'mySequence' (73f29b112f43466db29b112f43866d85)
[
    "78895e1d1af84fcd895e1d1af86fcdf2",
    "f73e7859ceb2428dbe7859ceb2328db1"
]
```

So invoking a sequence will result in n+1 activations, where n is how many actions are composed in the sequence. In each individual activation, it is transparent of the others, and openwhisk passes the json payload to the next function in the sequence.

In the original SeBS implementation, the `__main__` python file is used to wrap around the singular action file and will return the serverless function payload and the obtained metrics. The problem with the current implementation is that the payload of the action is an inner map of the payload map and this breaks how openwhisk does parameter passing between sequences, so we cannot simply have the sequence impl be a wsk invoke sequence.

Since we still want action-granularity metrics within the sequence, in addition to the sequence metrics itself, we need to handle sequence activations differently. Suppose we have the sequence S which comprises of actions a into b. We will have to wrap action a and b's payload as an extension of the map, and make sure that there are no parameter naming conflicts as well. Each action will be treated as a SeBS openwhisk action invocation.

It would go as follows:

create action a, with wrapping ==> a' (wherein payload is not nested mapping)
create action b, with wrapping ==> b' (wherein payload is not nested mapping)
create sequence S, as a' -> b'
SeBS invokes sequence S ==> a' -> b'

To avoid breaking compatability with the existing codebase, we will create a special case just for openwhisk sequence handling. We would name the mapping metrics based off the action's name.

In the benchmark configuration, the `config.json` file would now include a list of action names in order of activation.