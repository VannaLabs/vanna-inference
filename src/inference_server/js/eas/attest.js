#!/usr/bin/node
import { EAS, Offchain, SchemaEncoder, SchemaRegistry } from "@ethereum-attestation-service/eas-sdk";
import { ethers } from 'ethers';

function inferenceAttestation(m, p, r) {

  const EASContractAddress = "0xC2679fBD37d54388Ce493F1DB75320D236e1815e"; 
  const provider = ethers.providers.getDefaultProvider(
    "sepolia"
  );

  console.log('provider: ', provider)
  const eas = new EAS(EASContractAddress);
  eas.connect(provider);

  const offchain = await eas.getOffchain();

  const schemaEncoder = new SchemaEncoder("string modelhash, string params, string result");
  const encodedData = schemaEncoder.encodeData([
  { name: "modelhash", value: m, type: "string" },
  { name: "params", value: p, type: "string" },
  { name: "result", value: r, type: "string" },
  ]);

  const offchainAttestation = await offchain.signOffchainAttestation({
    recipient: '0x0000000000000000000000000000000000000000',
    expirationTime: 0,
    time: Date.now(),
    revocable: false,
    version: 1,
    nonce: 0,
    // Created inference attestation schema here on Sepolia
    schema: "0x4ebe8403ef1adcca038118c856741eb16a499568ae536e70ee2d4edbdee849e1",
    refUID: '0x0000000000000000000000000000000000000000000000000000000000000000',
    data: encodedData,
    }, "0x83FFe2cbe305cCD48836b64726BdfD1fB643A13a");
  return offchainAttestation
}

/*
EAS Offchain Attestation:
{"sig":{"domain":{"name":"EAS Attestation","version":"0.26","chainId":11155111,"verifyingContract":"0xC2679fBD37d54388Ce493F1DB75320D236e1815e"},"primaryType":"Attest","types":{"Attest":[{"name":"version","type":"uint16"},{"name":"schema","type":"bytes32"},{"name":"recipient","type":"address"},{"name":"time","type":"uint64"},{"name":"expirationTime","type":"uint64"},{"name":"revocable","type":"bool"},{"name":"refUID","type":"bytes32"},{"name":"data","type":"bytes"}]},"signature":{"r":"0x6988b707db3fc146c401035e8fd95e22c7aa8aa2ed6f6f480e7afcf6360d746c","s":"0x1bd44496a1bcfeed0d2947cf14b7af321c307d9a4f6aa48a34f0ac6976977c14","v":27},"uid":"0x5d490d5a276dbee5a61997d0d75ea85ef344f48798347b836e8926f5822c6efc","message":{"version":1,"schema":"0x4ebe8403ef1adcca038118c856741eb16a499568ae536e70ee2d4edbdee849e1","recipient":"0x0000000000000000000000000000000000000000","time":1691770616,"expirationTime":0,"refUID":"0x0000000000000000000000000000000000000000000000000000000000000000","revocable":false,"data":"0x000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000a566f6c6174696c6974790000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000365b5b302e30335d2c5b302e30355d2c5b302e30343035363638355d2c5b302e30333233353837315d2c5b302e30353632393537385d5d00000000000000000000000000000000000000000000000000000000000000000000000000000000000b302e303533313736313934000000000000000000000000000000000000000000","nonce":0}},"signer":"0x83FFe2cbe305cCD48836b64726BdfD1fB643A13a"}
*/