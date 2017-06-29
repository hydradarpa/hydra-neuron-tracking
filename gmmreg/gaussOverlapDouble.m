function  [fself, gself,f2,g2]= gaussOverlapDouble(A,B,scales,limit)

%Jeff N's version of the mex_GaussTransform from GMM mixturemodel code. I'm
%adding possibility to change scales and making it more transparent. The
%code takes point sets A and B, puts a gaussian at each position of with
%standard deviation given by scale, and then calculates the inner product.
%NOTE: this is not the full inner product as it skips the prefactor in
%front of the exponential term. This makes it so that the inner product of
%a gaussian with itself is 1. This is done to match the mex program
%exactly. Speed is now slightly faster than mex_GaussTransform

% inputs:   A pointset of scene, If A is n*3, scales and peaks are
% specified sepearately. if A is n*4, the 4th D is the scales, if A is n*5,
% 5th D is the peaks 
%           B pointset of model, same format as A;
%           scale is the variances of each point. if it is scalar, all
%           points will have the same varaince, if it is a cell, the first
%           cell will be the scales for the points in A, the second will be
%           the scales for the points in B

% outputs : f total overlap integrals
%            g gradient in energy of the points in A
   
% GaussOverlapDouble also calculates the self energy and repulsion, as if
% you used gaussOverlap twice, once with the model to itself and then again
% from model to scene, this has a small speed boost.

Apoints=size(A,1);Bpoints=size(B,1);
nPoints=Apoints*Bpoints;

if nargin<4
    limit=30; %should normally be Inf
end

peaksA=A(:,3);
peaksB=B(:,3);
peaksA=peaksA/sum(peaksA);
peaksB=peaksB/sum(peaksB);
peaksMat=bsxfun(@times, peaksA,[peaksA;peaksB]');

varMat=bsxfun(@plus,scales{1}.^2,([scales{1}; scales{2}]').^2);

A1=A(:,1:2);B1=B(:,1:2);
Bp=permute([A1;B1],[3,1,2]);
A1=permute(A1,[1,3,2]);
dmatAll=bsxfun(@minus,A1,Bp);
dmat2=sum(dmatAll.^2,3);
%Bp=permute([A1;B1],[3,1,2]);
%A1=permute(A1,[1,3,2]);
%dmatAll=bsxfun(@minus,A1,Bp);
%dmat2=sum(dmatAll.^2,3);

%% overlap of gaussians is a gaussian of the distance with variance as the sum
% of variances

% gradient of that overlap (d expMat/ dA) is force

%expMat=peaksMat./sqrt(2*pi*varMat).*exp(-1/2 * dmat.^2./varMat);
expMat=peaksMat.*exp(-2 * dmat2./varMat);

if ~isinf(limit)
    expMat(dmat2>limit.^2)=0;
end

expMatSelf=expMat(:,1:Apoints);
expMat1=expMat(:,Apoints+1:end);

fself=sum(expMatSelf(:));
f2=sum(expMat1(:));
expMat2=-(4./(varMat)).*expMat;
fmat=bsxfun(@times,expMat2,dmatAll);
gself=reshape(sum(fmat(:,1:Apoints,:),2),Apoints,3);
g2=reshape(sum(fmat(:,Apoints+1:end,:),2),Apoints,3);




